from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..core.response import success
from ..database import get_db
from ..models.asset import Asset
from ..models.asset_record import AssetRecord
from ..models.employee import Employee
from ..models.user import User
from ..schemas.record import RecordOut

router = APIRouter(prefix="/api/record", tags=["领用记录"], dependencies=[Depends(get_current_user)])


@router.get("/list", summary="分页查询领用记录")
def list_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    asset_name: str = Query("", description="资产名称（模糊查询）"),
    action: str = Query("", description="动作（领用/归还）"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            AssetRecord,
            Asset.asset_no,
            Asset.name.label("asset_name"),
            Employee.name.label("employee_name"),
            User.real_name.label("operator_name"),
        )
        .join(Asset, AssetRecord.asset_id == Asset.id)
        .join(Employee, AssetRecord.employee_id == Employee.id)
        .outerjoin(User, AssetRecord.operator_id == User.id)
    )
    if asset_name:
        query = query.filter(Asset.name.like(f"%{asset_name}%"))
    if action:
        query = query.filter(AssetRecord.action == action)
    total = query.count()
    rows = query.order_by(AssetRecord.id.desc()).offset((page - 1) * size).limit(size).all()
    items = [
        RecordOut(
            id=record.id,
            asset_id=record.asset_id,
            asset_no=asset_no,
            asset_name=asset_name_value,
            employee_id=record.employee_id,
            employee_name=employee_name,
            action=record.action,
            operator_name=operator_name,
            remark=record.remark,
            create_time=record.create_time,
        )
        for record, asset_no, asset_name_value, employee_name, operator_name in rows
    ]
    return success({"total": total, "items": [item.model_dump() for item in items]})
