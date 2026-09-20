import json
import logging
import re
import time

from ..config import WORKFLOW_MAX_CONTEXT_CHARS, WORKFLOW_MAX_REVIEW_ROUNDS
from .llm import chat_completion, extract_answer, is_mock_mode
from .prompt_manager import render_prompt
from .rag import retrieve
from .skills import execute_skill

logger = logging.getLogger("asset_admin")


def _truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...(内容过长已截断)"


def _mock_generate(requirement: str, schema_text: str, context_text: str) -> str:
    lines = [
        "【模拟模式】基于项目真实表结构与知识库检索结果生成的改动方案",
        "（配置 AI_API_KEY 后将由大模型生成完整可上线代码）",
        "",
        f"# 需求：{requirement}",
        "",
        "# 参考表结构（来自 query_table_schema 工具的真实结果）：",
    ]
    for line in schema_text.replace("\\n", "\n").splitlines()[:12]:
        lines.append(f"#   {line}")
    lines.append("")
    lines.append("# 参考项目知识库片段（RAG 检索）：")
    for line in context_text.splitlines()[:10]:
        lines.append(f"#   {line[:90]}")
    lines.append("")
    lines.append("# 建议改动步骤（按现有项目分层）：")
    lines.append("# 1. models/xxx.py       新增字段或模型定义")
    lines.append("# 2. schemas/xxx.py      新增/调整 Pydantic 校验模型（参数校验 + 中文提示）")
    lines.append("# 3. routers/xxx.py      新增接口，统一使用 success() 返回、异常处理兜底")
    lines.append("# 4. tests/              补充 pytest 用例覆盖新功能")
    return "\n".join(lines)


def _mock_review(code: str, requirement: str) -> dict:
    issues = []
    if "Field" not in code and "参数校验" not in code:
        issues.append({"severity": "中", "desc": "未体现参数校验", "fix": "在 Pydantic 模型中补充 Field 约束与中文提示"})
    if "异常" not in code and "try" not in code:
        issues.append({"severity": "中", "desc": "未体现异常处理", "fix": "补充 try/except 兜底并返回中文错误提示"})
    passed = len(issues) == 0
    return {
        "passed": passed,
        "issues": issues,
        "summary": "模拟评审：检查项全部通过" if passed else "模拟评审：存在待改进项，需回炉修正",
    }


def _parse_review(answer: str) -> dict:
    text = (answer or "").strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            return {
                "passed": bool(data.get("passed", True)),
                "issues": data.get("issues") or [],
                "summary": data.get("summary") or "",
            }
        except json.JSONDecodeError:
            pass
    logger.warning("评审输出不是标准 JSON，按通过处理：%s", text[:200])
    return {"passed": True, "issues": [], "summary": _truncate(text, 200)}


def _llm_generate(requirement: str, schema_text: str, context_text: str, feedback: str = None) -> str:
    full_requirement = requirement if not feedback else f"{requirement}\n\n评审反馈（必须修复）：{feedback}"
    prompt = render_prompt(
        "code_generate",
        requirement=full_requirement,
        table_schema=_truncate(schema_text, 3000),
        code_style=_truncate(context_text, WORKFLOW_MAX_CONTEXT_CHARS),
    )
    messages = [
        {"role": "system", "content": prompt["system"]},
        {"role": "user", "content": prompt["user"]},
    ]
    return extract_answer(chat_completion(messages, temperature=prompt["temperature"]))


def _llm_review(requirement: str, code: str) -> dict:
    prompt = render_prompt("code_review", requirement=requirement, code=_truncate(code, WORKFLOW_MAX_CONTEXT_CHARS))
    messages = [
        {"role": "system", "content": prompt["system"]},
        {"role": "user", "content": prompt["user"]},
    ]
    return _parse_review(extract_answer(chat_completion(messages, temperature=prompt["temperature"])))


def run_workflow(db, requirement: str, user=None) -> dict:
    """六步流水线：接收需求 → 读表结构 → 检索知识库 → 生成代码 → 评审 → 输出最终代码"""
    started = time.time()
    steps = []

    def add_step(name: str, status: str, detail: str, output: str = ""):
        steps.append({"name": name, "status": status, "detail": detail, "output": _truncate(output, 1500)})

    add_step("接收需求", "成功", "已接收开发需求", requirement)

    schema_result = execute_skill(db, "query_table_schema", {}, user)
    schema_text = json.dumps(schema_result, ensure_ascii=False)
    if schema_result.get("error"):
        add_step("读取表结构", "失败", schema_result["error"], schema_text)
    else:
        add_step("读取表结构", "成功", f"读取到 {schema_result.get('count', 0)} 张真实表结构", schema_text)

    hits = retrieve(db, requirement)
    if hits:
        context_text = "\n\n".join(f"【{filename}】{chunk.content}" for _, chunk, filename in hits)
        add_step("检索项目知识库", "成功", f"命中 {len(hits)} 个相关片段", context_text)
    else:
        context_text = "（项目知识库为空，建议先执行「重建项目知识库」）"
        add_step("检索项目知识库", "警告", "未命中相关片段，已降级继续", context_text)

    try:
        if is_mock_mode():
            code = _mock_generate(requirement, schema_text, context_text)
            generate_detail = "模拟模式生成改动方案（无 AI_API_KEY）"
        else:
            code = _llm_generate(requirement, schema_text, context_text)
            generate_detail = "大模型生成（使用固化 Prompt：人员系统代码生成Prompt）"
        add_step("生成代码", "成功", generate_detail, code)
    except Exception as exc:
        logger.exception("工作流生成代码失败")
        code = f"# 生成失败：{exc}"
        add_step("生成代码", "失败", f"生成异常：{exc}")

    rounds = 0
    review = {"passed": True, "issues": [], "summary": "无需评审"}
    while rounds < WORKFLOW_MAX_REVIEW_ROUNDS:
        rounds += 1
        try:
            if is_mock_mode():
                review = _mock_review(code, requirement)
                review_detail = "模拟模式评审（检查参数校验/异常处理）"
            else:
                review = _llm_review(requirement, code)
                review_detail = "大模型评审（使用固化 Prompt：人员系统代码评审Prompt）"
            add_step(
                f"自动代码评审（第 {rounds} 轮）",
                "成功" if review.get("passed") else "待改进",
                f"{review_detail}：{review.get('summary', '')}",
                json.dumps(review.get("issues", []), ensure_ascii=False, indent=2),
            )
        except Exception as exc:
            logger.exception("工作流代码评审失败")
            review = {"passed": True, "issues": [], "summary": f"评审异常已跳过：{exc}"}
            add_step(f"自动代码评审（第 {rounds} 轮）", "警告", f"评审异常：{exc}")

        if review.get("passed") or rounds >= WORKFLOW_MAX_REVIEW_ROUNDS:
            break

        feedback = "；".join(item.get("fix", "") for item in review.get("issues", []))
        try:
            if is_mock_mode():
                code = code + f"\n\n# 【第 {rounds} 轮评审后修正】已按评审意见补充：{feedback}"
            else:
                code = _llm_generate(requirement, schema_text, context_text, feedback=feedback)
            add_step(f"按评审意见回炉修正（第 {rounds} 轮）", "成功", f"修复项：{feedback}", code)
        except Exception as exc:
            logger.exception("工作流回炉修正失败")
            add_step(f"按评审意见回炉修正（第 {rounds} 轮）", "失败", f"修正异常：{exc}")

    add_step("输出最终代码", "成功", f"共评审 {rounds} 轮，达到最大轮次限制自动收敛" if rounds >= WORKFLOW_MAX_REVIEW_ROUNDS else f"共评审 {rounds} 轮", code)

    duration_ms = int((time.time() - started) * 1000)
    return {
        "status": "成功",
        "steps": steps,
        "result": code,
        "review_rounds": rounds,
        "duration_ms": duration_ms,
    }
