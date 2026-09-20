import json
import logging
import re
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..config import MAX_UPLOAD_SIZE, UPLOAD_DIR
from ..core.deps import get_current_user, require_admin
from ..core.llm import chat_completion, extract_answer, is_mock_mode
from ..core.logger import log_operation
from ..core.prompt_manager import list_prompts, reload_prompts
from ..core.prompts import QA_ANSWER_TEMPERATURE, SYSTEM_PROMPT_QA, SYSTEM_PROMPT_TOOL, TOOL_ANSWER_TEMPERATURE
from ..core.rag import parse_document, reindex_project, retrieve, split_text
from ..core.response import fail, success
from ..core.skills import execute_skill, list_skills, tool_definitions
from ..core.workflow import run_workflow
from ..database import get_db
from ..models.ai import AiChunk, AiDocument, AiWorkflowRun
from ..models.user import User
from ..schemas.ai import AskRequest, ChatRequest, DocumentOut, SkillRunRequest, WorkflowRequest

logger = logging.getLogger("asset_admin")

router = APIRouter(prefix="/api/ai", tags=["AI 助手"], dependencies=[Depends(get_current_user)])

AI_DOC_DIR = UPLOAD_DIR / "ai_docs"
AI_DOC_EXTENSIONS = {".txt", ".md", ".docx"}

TOOL_LABELS = {
    "query_employees": "员工",
    "query_assets": "资产",
    "query_records": "领用记录",
    "query_table_schema": "表结构",
    "read_project_file": "项目文件",
}

TABLE_HINTS = {
    "员工表": "employee",
    "资产表": "asset",
    "领用记录表": "asset_record",
    "记录表": "asset_record",
    "用户表": "user",
    "角色表": "role",
    "知识库": "ai_document",
}

FILE_HINTS = [
    (["员工", "用户"], "backend/app/routers/employee.py"),
    (["资产", "设备"], "backend/app/routers/asset.py"),
    (["登录", "认证", "鉴权"], "backend/app/routers/auth.py"),
    (["配置"], "backend/app/config.py"),
    (["表", "数据库"], "sql/init.sql"),
    (["页面", "前端"], "backend/app/static/index.html"),
]


@router.post("/document", summary="上传知识库文档（txt/md/docx）")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    filename = file.filename or "未命名文档"
    extension = Path(filename).suffix.lower()
    if extension not in AI_DOC_EXTENSIONS:
        raise HTTPException(status_code=400, detail="知识库仅支持 txt / md / docx 格式")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")
    text = parse_document(filename, data)
    chunks = split_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="文档解析后没有有效内容")
    AI_DOC_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = AI_DOC_DIR / f"{uuid.uuid4().hex}{extension}"
    stored_path.write_bytes(data)
    document = AiDocument(
        filename=filename,
        file_path=str(stored_path),
        file_size=len(data),
        chunk_count=len(chunks),
        category="upload",
        uploader_id=admin.id,
    )
    db.add(document)
    db.flush()
    db.add_all([AiChunk(document_id=document.id, seq=index, content=content) for index, content in enumerate(chunks)])
    db.commit()
    db.refresh(document)
    log_operation(admin, "上传知识库文档", f"{filename}（{len(chunks)} 个切片）")
    return success(DocumentOut.model_validate(document), msg="文档上传成功")


@router.get("/document/list", summary="知识库文档列表")
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(AiDocument).order_by(AiDocument.id.desc()).all()
    items = []
    for document in documents:
        item = DocumentOut.model_validate(document).model_dump()
        item["category"] = document.category or "upload"
        items.append(item)
    return success(items)


@router.delete("/document/{doc_id}", summary="删除知识库文档")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    document = db.get(AiDocument, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    db.query(AiChunk).filter(AiChunk.document_id == doc_id).delete()
    if (document.category or "upload") == "upload":
        try:
            Path(document.file_path).unlink(missing_ok=True)
        except OSError:
            logger.warning("删除知识库文件失败: %s", document.file_path)
    filename = document.filename
    db.delete(document)
    db.commit()
    log_operation(admin, "删除知识库文档", filename)
    return success(msg="删除成功")


@router.post("/project/reindex", summary="重建项目知识库（扫描项目文档与代码）")
def project_reindex(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    stats = reindex_project(db, uploader_id=admin.id)
    log_operation(admin, "重建项目知识库", f"文件 {stats['files']} 个，切片 {stats['chunks']} 个")
    return success(stats, msg=f"入库完成：{stats['files']} 个文件、{stats['chunks']} 个切片")


@router.get("/prompt/list", summary="查看固化的提示词")
def prompt_list():
    return success(list_prompts())


@router.post("/prompt/reload", summary="重新加载提示词配置")
def prompt_reload(admin: User = Depends(require_admin)):
    items = reload_prompts()
    log_operation(admin, "重载提示词配置", f"{len(items)} 个")
    return success(items, msg="提示词配置已重新加载")


@router.get("/skill/list", summary="查看已注册的 Skills")
def skill_list():
    return success(list_skills())


@router.post("/skill/run", summary="直接执行 Skill（调试用）")
def skill_run(
    data: SkillRunRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = execute_skill(db, data.name, data.arguments, admin)
    log_operation(admin, "执行Skill", f"{data.name} {json.dumps(data.arguments, ensure_ascii=False)}")
    if result.get("error"):
        return fail(msg=result["error"], code=400)
    return success(result)


@router.post("/ask", summary="知识库问答（RAG）")
def ask(
    data: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hits = retrieve(db, data.question, top_k=data.top_k)
    sources = [
        {"document": filename, "score": round(score, 3), "snippet": chunk.content[:120]}
        for score, chunk, filename in hits
    ]
    if not hits:
        answer = "知识库中没有找到相关信息，请先上传业务文档或重建项目知识库，或换一种问法。"
    elif is_mock_mode():
        lines = ["【模拟模式】根据知识库检索到以下相关内容："]
        lines.extend(f"- {chunk.content[:150]}" for _, chunk, _ in hits)
        lines.append("（在 config.py 中配置 AI_API_KEY 后可切换为真实大模型总结回答）")
        answer = "\n".join(lines)
    else:
        context = "\n\n".join(f"【来源：{filename}】{chunk.content}" for _, chunk, filename in hits)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_QA},
            {"role": "user", "content": f"参考资料：\n{context}\n\n问题：{data.question}"},
        ]
        answer = extract_answer(chat_completion(messages, temperature=QA_ANSWER_TEMPERATURE))
    log_operation(user, "知识库问答", data.question)
    return success({"answer": answer, "sources": sources, "mode": "mock" if is_mock_mode() else "real"})


def _extract_file_path(message: str) -> str:
    match = re.search(r"[\w./\\-]+\.(?:py|sql|md|json|yaml|html|js|css|txt|bat)", message)
    if match:
        return match.group(0).replace("\\", "/")
    for keywords, path in FILE_HINTS:
        if any(keyword in message for keyword in keywords):
            return path
    return "README.md"


def _mock_tool_call(message: str):
    if any(keyword in message for keyword in ["记录", "领用记录", "归还记录"]):
        arguments = {}
        if "领用" in message:
            arguments["action"] = "领用"
        if "归还" in message:
            arguments["action"] = "归还"
        return "query_records", arguments
    if any(keyword in message for keyword in ["表结构", "字段", "数据库表", "有哪些表"]):
        arguments = {}
        for hint, table in TABLE_HINTS.items():
            if hint in message:
                arguments["table"] = table
                break
        return "query_table_schema", arguments
    if any(keyword in message for keyword in ["代码", "文件", "源码"]):
        return "read_project_file", {"path": _extract_file_path(message)}
    if "资产" in message or "设备" in message:
        arguments = {}
        for status in ["空闲", "已领用", "维修", "报废"]:
            if status in message:
                arguments["status"] = status
                break
        for category in ["电脑设备", "网络设备", "办公用品"]:
            if category in message:
                arguments["category"] = category
                break
        return "query_assets", arguments
    arguments = {}
    for department in ["技术部", "人事部", "财务部", "市场部", "行政部"]:
        if department in message:
            arguments["department"] = department
            break
    if "在职" in message:
        arguments["status"] = "在职"
    if "离职" in message:
        arguments["status"] = "离职"
    return "query_employees", arguments


def _format_mock_answer(tool_name: str, result: dict) -> str:
    if result.get("error"):
        return f"【模拟模式】工具执行失败：{result['error']}"
    if tool_name == "query_table_schema":
        lines = [f"【模拟模式】读取到 {result.get('count', 0)} 张真实表结构："]
        for table in result.get("tables", [])[:5]:
            field_names = "、".join(field["字段"] for field in table["字段"][:8])
            lines.append(f"- {table['表名']}（{table['字段数']} 个字段）：{field_names} ...")
        lines.append("（配置 AI_API_KEY 后由大模型组织完整回答）")
        return "\n".join(lines)
    if tool_name == "read_project_file":
        if result.get("path"):
            preview = (result.get("content") or "")[:400]
            return (
                f"【模拟模式】已读取项目文件 {result['path']}"
                f"（{result.get('size', 0)} 字节，截断={result.get('truncated')}）：\n{preview}\n"
                "（配置 AI_API_KEY 后由大模型总结代码逻辑）"
            )
        return "【模拟模式】文件读取失败。"
    label = TOOL_LABELS.get(tool_name, "数据")
    if not result.get("count"):
        return f"【模拟模式】没有查询到符合条件的{label}数据。"
    lines = [f"【模拟模式】共查询到 {result['count']} 条{label}数据："]
    for item in result["items"][:5]:
        lines.append("、".join(f"{key}：{value}" for key, value in item.items() if value is not None))
    lines.append("（在 config.py 中配置 AI_API_KEY 后可切换为真实大模型智能回答）")
    return "\n".join(lines)


@router.post("/chat", summary="数据助手（大模型工具调用）")
def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tool_info = None
    result = None
    if is_mock_mode():
        tool_name, arguments = _mock_tool_call(data.message)
        result = execute_skill(db, tool_name, arguments, user)
        answer = _format_mock_answer(tool_name, result)
        tool_info = {"name": tool_name, "arguments": arguments}
    else:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_TOOL},
            {"role": "user", "content": data.message},
        ]
        response = chat_completion(messages, tools=tool_definitions(), temperature=TOOL_ANSWER_TEMPERATURE)
        try:
            message = response["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            logger.error("AI 返回格式异常: %s", str(response)[:300])
            raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后重试")
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            call = tool_calls[0]
            tool_name = call["function"]["name"]
            try:
                arguments = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            result = execute_skill(db, tool_name, arguments, user)
            tool_info = {"name": tool_name, "arguments": arguments}
            messages.append({"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", "call_1"),
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
            answer = extract_answer(chat_completion(messages, temperature=TOOL_ANSWER_TEMPERATURE))
        else:
            answer = message.get("content") or ""
    log_operation(user, "AI 数据助手", data.message)
    return success({"answer": answer, "tool": tool_info, "data": result, "mode": "mock" if is_mock_mode() else "real"})


@router.post("/workflow", summary="AI 自动开发工作流（Agent）")
def run_agent_workflow(
    data: WorkflowRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    started = time.time()
    try:
        outcome = run_workflow(db, data.requirement, user)
        run = AiWorkflowRun(
            requirement=data.requirement,
            status=outcome["status"],
            review_rounds=outcome["review_rounds"],
            steps=json.dumps(outcome["steps"], ensure_ascii=False),
            result=outcome["result"],
            duration_ms=outcome["duration_ms"],
            operator_id=user.id,
        )
    except Exception as exc:
        logger.exception("工作流执行异常")
        run = AiWorkflowRun(
            requirement=data.requirement,
            status="失败",
            review_rounds=0,
            steps=json.dumps([{"name": "执行异常", "status": "失败", "detail": str(exc)}], ensure_ascii=False),
            result=None,
            duration_ms=int((time.time() - started) * 1000),
            operator_id=user.id,
        )
    db.add(run)
    db.commit()
    db.refresh(run)
    log_operation(user, "AI自动开发工作流", f"{data.requirement}（{run.status}，评审 {run.review_rounds} 轮）")
    return success(
        {
            "id": run.id,
            "status": run.status,
            "review_rounds": run.review_rounds,
            "duration_ms": run.duration_ms,
            "steps": json.loads(run.steps or "[]"),
            "result": run.result,
        }
    )


@router.get("/workflow/list", summary="工作流运行记录")
def workflow_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
):
    query = db.query(AiWorkflowRun).order_by(AiWorkflowRun.id.desc())
    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()
    items = [
        {
            "id": row.id,
            "requirement": row.requirement,
            "status": row.status,
            "review_rounds": row.review_rounds,
            "duration_ms": row.duration_ms,
            "create_time": row.create_time,
        }
        for row in rows
    ]
    return success({"total": total, "items": items})


@router.get("/workflow/{run_id}", summary="工作流运行详情")
def workflow_detail(run_id: int, db: Session = Depends(get_db)):
    run = db.get(AiWorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    return success(
        {
            "id": run.id,
            "requirement": run.requirement,
            "status": run.status,
            "review_rounds": run.review_rounds,
            "duration_ms": run.duration_ms,
            "steps": json.loads(run.steps or "[]"),
            "result": run.result,
            "create_time": run.create_time,
        }
    )
