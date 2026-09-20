import logging

from sqlalchemy import inspect

from ..config import PROJECT_ROOT, SKILL_ALLOWED_EXTENSIONS, SKILL_FILE_MAX_BYTES, SKILL_FILE_MAX_CHARS
from ..models.asset import Asset
from ..models.asset_record import AssetRecord
from ..models.employee import Employee

logger = logging.getLogger("asset_admin")

SKILLS = {}


def register_skill(name: str, description: str, parameters: dict, handler, admin_only: bool = False):
    """Skill 标准结构：名称 / 描述 / 参数规范 / 执行逻辑 / 权限"""
    SKILLS[name] = {
        "name": name,
        "description": description,
        "parameters": parameters,
        "handler": handler,
        "admin_only": admin_only,
    }


def list_skills() -> list:
    return [
        {
            "name": skill["name"],
            "description": skill["description"],
            "parameters": skill["parameters"],
            "admin_only": skill["admin_only"],
        }
        for skill in SKILLS.values()
    ]


def tool_definitions() -> list:
    """生成大模型 Function Calling 的工具定义"""
    return [
        {
            "type": "function",
            "function": {
                "name": skill["name"],
                "description": skill["description"],
                "parameters": skill["parameters"],
            },
        }
        for skill in SKILLS.values()
    ]


def execute_skill(db, name: str, arguments: dict, user=None) -> dict:
    """统一执行入口：未知工具拒绝、权限校验、异常兜底"""
    skill = SKILLS.get(name)
    if not skill:
        return {"error": f"未知工具：{name}"}
    if skill["admin_only"] and (user is None or not user.has_role("admin")):
        return {"error": "权限不足：该工具仅管理员可调用"}
    try:
        return skill["handler"](db, arguments or {})
    except Exception as exc:
        logger.exception("Skill 执行失败：%s", name)
        return {"error": f"工具执行失败：{exc}"}


def _query_employees(db, arguments: dict) -> dict:
    limit = min(int(arguments.get("limit") or 5), 20)
    query = db.query(Employee)
    if arguments.get("name"):
        query = query.filter(Employee.name.like(f"%{arguments['name']}%"))
    if arguments.get("department"):
        query = query.filter(Employee.department == arguments["department"])
    if arguments.get("status"):
        query = query.filter(Employee.status == arguments["status"])
    rows = query.order_by(Employee.id.desc()).limit(limit).all()
    return {
        "count": len(rows),
        "items": [
            {"工号": r.emp_no, "姓名": r.name, "部门": r.department, "职位": r.position, "状态": r.status}
            for r in rows
        ],
    }


def _query_assets(db, arguments: dict) -> dict:
    limit = min(int(arguments.get("limit") or 5), 20)
    query = db.query(Asset)
    if arguments.get("name"):
        query = query.filter(Asset.name.like(f"%{arguments['name']}%"))
    if arguments.get("status"):
        query = query.filter(Asset.status == arguments["status"])
    if arguments.get("category"):
        query = query.filter(Asset.category == arguments["category"])
    rows = query.order_by(Asset.id.desc()).limit(limit).all()
    return {
        "count": len(rows),
        "items": [
            {"资产编号": r.asset_no, "名称": r.name, "类别": r.category, "状态": r.status}
            for r in rows
        ],
    }


def _query_records(db, arguments: dict) -> dict:
    limit = min(int(arguments.get("limit") or 5), 20)
    query = db.query(AssetRecord, Asset.name.label("asset_name"), Employee.name.label("employee_name")).join(
        Asset, AssetRecord.asset_id == Asset.id
    ).join(Employee, AssetRecord.employee_id == Employee.id)
    if arguments.get("asset_name"):
        query = query.filter(Asset.name.like(f"%{arguments['asset_name']}%"))
    if arguments.get("action"):
        query = query.filter(AssetRecord.action == arguments["action"])
    rows = query.order_by(AssetRecord.id.desc()).limit(limit).all()
    return {
        "count": len(rows),
        "items": [
            {"资产名称": asset_name, "操作": record.action, "领用人": employee_name}
            for record, asset_name, employee_name in rows
        ],
    }


def _query_table_schema(db, arguments: dict) -> dict:
    inspector = inspect(db.get_bind())
    table_filter = (arguments.get("table") or "").strip()
    tables = sorted(inspector.get_table_names())
    if table_filter:
        tables = [name for name in tables if name == table_filter]
        if not tables:
            return {"error": f"表不存在：{table_filter}", "count": 0, "tables": []}
    result = []
    for table in tables:
        columns = [
            {
                "字段": column["name"],
                "类型": str(column["type"]),
                "可空": bool(column.get("nullable", True)),
                "说明": column.get("comment") or "",
            }
            for column in inspector.get_columns(table)
        ]
        result.append({"表名": table, "字段数": len(columns), "字段": columns})
    return {"count": len(result), "tables": result}


def _read_project_file(db, arguments: dict) -> dict:
    relative = (arguments.get("path") or "").strip().replace("\\", "/")
    if not relative:
        return {"error": "请提供文件路径（相对项目根目录）"}
    target = (PROJECT_ROOT / relative).resolve()
    root = PROJECT_ROOT.resolve()
    if not str(target).startswith(str(root)):
        return {"error": "非法路径：只允许读取项目目录内的文件"}
    if target.suffix.lower() not in SKILL_ALLOWED_EXTENSIONS:
        return {"error": f"不支持读取该类型文件：{target.suffix or '（无扩展名）'}"}
    if not target.exists() or not target.is_file():
        return {"error": f"文件不存在：{relative}"}
    if target.stat().st_size > SKILL_FILE_MAX_BYTES:
        return {"error": "文件过大，拒绝读取（超过 200KB）"}
    content = target.read_text(encoding="utf-8", errors="ignore")
    truncated = len(content) > SKILL_FILE_MAX_CHARS
    return {
        "path": relative,
        "size": target.stat().st_size,
        "truncated": truncated,
        "content": content[:SKILL_FILE_MAX_CHARS],
    }


register_skill(
    "query_employees",
    "按姓名、部门、状态查询员工信息",
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "员工姓名（模糊查询）"},
            "department": {"type": "string", "description": "部门名称"},
            "status": {"type": "string", "enum": ["在职", "离职"], "description": "在职状态"},
            "limit": {"type": "integer", "description": "返回条数，默认 5"},
        },
    },
    _query_employees,
)

register_skill(
    "query_assets",
    "按名称、状态、类别查询资产信息",
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "资产名称（模糊查询）"},
            "status": {"type": "string", "enum": ["空闲", "已领用", "维修", "报废"], "description": "资产状态"},
            "category": {"type": "string", "description": "资产类别"},
            "limit": {"type": "integer", "description": "返回条数，默认 5"},
        },
    },
    _query_assets,
)

register_skill(
    "query_records",
    "查询资产领用/归还记录",
    {
        "type": "object",
        "properties": {
            "asset_name": {"type": "string", "description": "资产名称（模糊查询）"},
            "action": {"type": "string", "enum": ["领用", "归还"], "description": "操作类型"},
            "limit": {"type": "integer", "description": "返回条数，默认 5"},
        },
    },
    _query_records,
)

register_skill(
    "query_table_schema",
    "查询数据库真实表结构（表名、字段、类型、注释），写代码前用它核对字段，避免编造",
    {
        "type": "object",
        "properties": {
            "table": {"type": "string", "description": "表名，不传则返回全部表"},
        },
    },
    _query_table_schema,
)

register_skill(
    "read_project_file",
    "读取项目内的代码/配置文件（如 backend/app/routers/employee.py），修改代码前先读原文件保持风格一致",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对项目根目录的文件路径"},
        },
        "required": ["path"],
    },
    _read_project_file,
    admin_only=True,
)
