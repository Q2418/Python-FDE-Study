from typing import Any

from fastapi.responses import JSONResponse

SUCCESS_CODE = 200
FAIL_CODE = 500


def success(data: Any = None, msg: str = "操作成功") -> dict:
    """成功返回：HTTP 200 + 统一格式"""
    return {"code": SUCCESS_CODE, "msg": msg, "data": data}


def fail(msg: str = "操作失败", code: int = FAIL_CODE, data: Any = None) -> JSONResponse:
    """失败返回：业务失败时使用，HTTP 状态码与 code 保持一致"""
    return JSONResponse(status_code=code, content={"code": code, "msg": msg, "data": data})


def custom(code: int, msg: str, data: Any = None) -> JSONResponse:
    """自定义返回：需要特殊业务码时使用"""
    return JSONResponse(status_code=code, content={"code": code, "msg": msg, "data": data})
