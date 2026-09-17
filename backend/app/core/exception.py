import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("asset_admin")

FIELD_NAMES = {
    "emp_no": "工号",
    "name": "名称",
    "gender": "性别",
    "department": "部门",
    "position": "职位",
    "phone": "手机号",
    "email": "邮箱",
    "hire_date": "入职日期",
    "status": "状态",
    "asset_no": "资产编号",
    "category": "类别",
    "brand": "品牌",
    "model": "型号",
    "price": "价格",
    "purchase_date": "购置日期",
    "user_id": "领用人",
    "remark": "备注",
    "page": "页码",
    "size": "每页条数",
}

TYPE_MESSAGES = {
    "missing": "不能为空",
    "string_too_short": "长度过短",
    "string_too_long": "长度超长",
    "string_pattern_mismatch": "格式不正确",
    "int_parsing": "必须是整数",
    "int_type": "必须是整数",
    "float_parsing": "必须是数字",
    "float_type": "必须是数字",
    "date_parsing": "日期格式不正确",
    "date_from_datetime_parsing": "日期格式不正确",
    "datetime_parsing": "日期格式不正确",
    "greater_than_equal": "数值过小",
    "less_than_equal": "数值过大",
    "enum": "取值不合法",
    "value_error": "格式不正确",
}


def format_validation_error(exc: RequestValidationError, path: str = "") -> str:
    """把 Pydantic 英文校验错误翻译成中文提示"""
    errors = exc.errors()
    if not errors:
        return "参数校验失败"
    field_names = FIELD_NAMES
    if "/employee" in path:
        field_names = {**FIELD_NAMES, "name": "姓名"}
    first = errors[0]
    loc = first.get("loc", ())
    raw_field = str(loc[-1]) if loc else "参数"
    field = field_names.get(raw_field, raw_field)
    etype = first.get("type", "")
    ctx = first.get("ctx") or {}

    if etype == "string_too_long":
        return f"{field}长度不能超过{ctx.get('max_length', '')}个字符"
    if etype == "string_too_short":
        return f"{field}长度不能少于{ctx.get('min_length', '')}个字符"
    if etype == "greater_than_equal":
        return f"{field}不能小于{ctx.get('ge', '')}"
    if etype == "less_than_equal":
        return f"{field}不能大于{ctx.get('le', '')}"
    if etype == "enum":
        return f"{field}取值不合法，可选值：{ctx.get('expected', '')}"
    return f"{field}{TYPE_MESSAGES.get(etype, first.get('msg', '参数不合法'))}"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "msg": str(exc.detail), "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "msg": f"参数错误：{format_validation_error(exc, request.url.path)}",
                "data": None,
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("数据库异常: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "msg": "数据库操作异常，请稍后重试", "data": None},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("系统异常: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "msg": "系统内部错误，请联系管理员", "data": None},
        )
