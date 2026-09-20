import logging

import yaml

from ..config import PROMPTS_FILE

logger = logging.getLogger("asset_admin")

DEFAULT_PROMPTS = {
    "code_generate": {
        "name": "人员系统代码生成Prompt（内置默认）",
        "version": "default",
        "temperature": 0.2,
        "system": "你是资深 Python 后端开发工程师，负责企业人员资产管理系统的迭代开发。",
        "user": (
            "【任务】{requirement}\n\n"
            "【约束】参考真实表结构，禁止编造字段；符合 FastAPI + SQLAlchemy 项目风格；做参数校验与异常处理。\n\n"
            "【项目表结构】\n{table_schema}\n\n"
            "【相关旧代码】\n{code_style}\n\n"
            "【输出格式】Markdown：改动说明 + 按文件的完整代码块。"
        ),
    },
    "code_review": {
        "name": "人员系统代码评审Prompt（内置默认）",
        "version": "default",
        "temperature": 0.1,
        "system": "你是资深代码评审工程师，负责企业人员资产管理系统的代码质量把关。",
        "user": (
            "【任务】评审以下代码（需求：{requirement}），找 bug、缺失校验、安全隐患。\n\n"
            "【待评审代码】\n{code}\n\n"
            '【输出格式】只输出 JSON：{{"passed": true/false, "issues": [], "summary": ""}}'
        ),
    },
}

_cache = {}


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def load_prompts(force: bool = False) -> dict:
    global _cache
    if _cache and not force:
        return _cache
    if PROMPTS_FILE.exists():
        try:
            data = yaml.safe_load(PROMPTS_FILE.read_text(encoding="utf-8")) or {}
            prompts = data.get("prompts") or {}
            if prompts:
                _cache = prompts
                logger.info("提示词配置加载成功：%s 个（文件版本 %s）", len(prompts), data.get("version", "-"))
                return _cache
        except Exception as exc:
            logger.error("提示词配置解析失败，使用内置默认值：%s", exc)
    else:
        logger.warning("提示词配置文件不存在，使用内置默认值：%s", PROMPTS_FILE)
    _cache = DEFAULT_PROMPTS
    return _cache


def get_prompt(key: str) -> dict:
    prompts = load_prompts()
    if key not in prompts:
        raise KeyError(f"提示词不存在：{key}")
    return prompts[key]


def render_prompt(key: str, **variables) -> dict:
    prompt = get_prompt(key)
    safe = _SafeDict(**variables)
    return {
        "key": key,
        "name": prompt.get("name", key),
        "version": prompt.get("version", "-"),
        "temperature": prompt.get("temperature", 0.2),
        "system": (prompt.get("system") or "").format_map(safe),
        "user": (prompt.get("user") or "").format_map(safe),
    }


def list_prompts() -> list:
    return [
        {
            "key": key,
            "name": item.get("name", key),
            "version": item.get("version", "-"),
            "temperature": item.get("temperature", 0.2),
        }
        for key, item in load_prompts().items()
    ]


def reload_prompts() -> list:
    load_prompts(force=True)
    return list_prompts()
