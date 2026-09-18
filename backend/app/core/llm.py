import logging

import httpx
from fastapi import HTTPException

from ..config import AI_API_KEY, AI_BASE_URL, AI_ENABLED, AI_MODEL, AI_TIMEOUT_SECONDS

logger = logging.getLogger("asset_admin")


def is_mock_mode() -> bool:
    """未配置 AI_API_KEY 时使用内置模拟模式"""
    return not AI_ENABLED


def chat_completion(messages: list, temperature: float = 0.3, tools: list = None) -> dict:
    """调用 OpenAI 兼容的 Chat Completions 接口（DeepSeek/通义/智谱等均可）"""
    payload = {"model": AI_MODEL, "messages": messages, "temperature": temperature}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    try:
        with httpx.Client(timeout=AI_TIMEOUT_SECONDS) as client:
            resp = client.post(
                f"{AI_BASE_URL.rstrip('/')}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {AI_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException:
        logger.error("AI 调用超时（%s 秒）", AI_TIMEOUT_SECONDS)
        raise HTTPException(status_code=504, detail="AI 服务响应超时，请稍后重试")
    except httpx.HTTPStatusError as exc:
        logger.error("AI 服务返回错误: HTTP %s %s", exc.response.status_code, exc.response.text[:200])
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败（HTTP {exc.response.status_code}）")
    except httpx.HTTPError as exc:
        logger.error("AI 服务网络异常: %s", exc)
        raise HTTPException(status_code=502, detail="AI 服务网络异常，请检查网络或配置")


def extract_answer(response: dict) -> str:
    try:
        return response["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        logger.error("AI 返回格式异常: %s", str(response)[:300])
        raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后重试")
