from ..models.asset import Asset
from ..models.asset_record import AssetRecord
from ..models.employee import Employee

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "query_employees",
            "description": "按姓名、部门、状态查询员工信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "员工姓名（模糊查询）"},
                    "department": {"type": "string", "description": "部门名称"},
                    "status": {"type": "string", "enum": ["在职", "离职"], "description": "在职状态"},
                    "limit": {"type": "integer", "description": "返回条数，默认 5"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_assets",
            "description": "按名称、状态、类别查询资产信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "资产名称（模糊查询）"},
                    "status": {"type": "string", "enum": ["空闲", "已领用", "维修", "报废"], "description": "资产状态"},
                    "category": {"type": "string", "description": "资产类别"},
                    "limit": {"type": "integer", "description": "返回条数，默认 5"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_records",
            "description": "查询资产领用/归还记录",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_name": {"type": "string", "description": "资产名称（模糊查询）"},
                    "action": {"type": "string", "enum": ["领用", "归还"], "description": "操作类型"},
                    "limit": {"type": "integer", "description": "返回条数，默认 5"},
                },
            },
        },
    },
]


def execute_tool(db, name: str, arguments: dict) -> dict:
    """执行大模型选择的工具函数，返回真实数据库结果"""
    limit = min(int(arguments.get("limit") or 5), 20)
    if name == "query_employees":
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
    if name == "query_assets":
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
    if name == "query_records":
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
    return {"count": 0, "items": [], "error": f"未知工具：{name}"}
