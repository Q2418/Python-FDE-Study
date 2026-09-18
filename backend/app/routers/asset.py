from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, load_only

from ..core.deps import get_current_user, require_admin
from ..core.logger import log_operation
from ..core.response import success
from ..database import get_db
from ..models.asset import Asset
from ..models.asset_record import AssetRecord
from ..models.employee import Employee
from ..models.user import User
from ..schemas.asset import AssetCreate, AssetListOut, AssetOut, AssetUpdate
from ..schemas.record import BorrowRequest, ReturnRequest

router = APIRouter(
    prefix="/api/asset",
    tags=["资产管理"],
    dependencies=[Depends(get_current_user)],
)

LIST_FIELDS = (
    Asset.id,
    Asset.asset_no,
    Asset.name,
    Asset.category,
    Asset.brand,
    Asset.model,
    Asset.price,
    Asset.purchase_date,
    Asset.status,
    Asset.user_id,
    Asset.remark,
)


def check_asset_conflict(db: Session, asset_no: str, name: str, exclude_id: int = None):
    """业务规则：资产编号、名称不允许重复"""
    query_no = db.query(Asset.id).filter(Asset.asset_no == asset_no)
    query_name = db.query(Asset.id).filter(Asset.name == name)
    if exclude_id is not None:
        query_no = query_no.filter(Asset.id != exclude_id)
        query_name = query_name.filter(Asset.id != exclude_id)
    if query_no.first():
        raise HTTPException(status_code=400, detail="资产编号已存在，请更换后重试")
    if query_name.first():
        raise HTTPException(status_code=400, detail="资产名称已存在，请勿重复录入")


SORT_FIELDS = {
    "id": Asset.id,
    "asset_no": Asset.asset_no,
    "name": Asset.name,
    "price": Asset.price,
    "purchase_date": Asset.purchase_date,
    "create_time": Asset.create_time,
}


@router.get("/list", summary="分页查询资产列表（多条件 + 排序）")
def list_assets(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    name: str = Query("", description="资产名称（模糊查询）"),
    status: str = Query("", description="状态（精准查询）"),
    category: str = Query("", description="类别（精准查询）"),
    sort_by: str = Query("id", description="排序字段：id/asset_no/name/price/purchase_date/create_time"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方式：asc/desc"),
    db: Session = Depends(get_db),
):
    query = db.query(Asset).options(load_only(*LIST_FIELDS))
    if name:
        query = query.filter(Asset.name.like(f"%{name}%"))
    if status:
        query = query.filter(Asset.status == status)
    if category:
        query = query.filter(Asset.category == category)
    sort_column = SORT_FIELDS.get(sort_by, Asset.id)
    order_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    total = query.count()
    items = query.order_by(order_clause).offset((page - 1) * size).limit(size).all()
    return success({"total": total, "items": [AssetListOut.model_validate(item) for item in items]})


@router.get("/{asset_id}", summary="查询单个资产")
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    return success(AssetOut.model_validate(asset))


@router.post("", summary="新增资产")
def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    check_asset_conflict(db, data.asset_no, data.name)
    asset = Asset(**data.model_dump())
    db.add(asset)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="资产编号已存在，请更换后重试")
    db.refresh(asset)
    log_operation(_admin, "新增资产", f"{asset.asset_no} {asset.name}")
    return success(AssetOut.model_validate(asset), msg="新增成功")


@router.put("/{asset_id}", summary="修改资产")
def update_asset(
    asset_id: int,
    data: AssetUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    update_data = data.model_dump(exclude_unset=True)
    check_asset_conflict(
        db,
        update_data.get("asset_no", asset.asset_no),
        update_data.get("name", asset.name),
        exclude_id=asset_id,
    )
    for key, value in update_data.items():
        setattr(asset, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="资产编号已存在，请更换后重试")
    db.refresh(asset)
    log_operation(_admin, "修改资产", f"{asset.asset_no} {asset.name} 字段：{'、'.join(update_data.keys())}")
    return success(AssetOut.model_validate(asset), msg="修改成功")


@router.delete("/{asset_id}", summary="删除资产")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    db.delete(asset)
    db.commit()
    log_operation(_admin, "删除资产", f"{asset.asset_no} {asset.name}")
    return success(msg="删除成功")


@router.post("/{asset_id}/borrow", summary="资产领用")
def borrow_asset(
    asset_id: int,
    data: BorrowRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    if asset.status != "空闲":
        raise HTTPException(status_code=400, detail=f"该资产当前状态为「{asset.status}」，无法领用")
    employee = db.get(Employee, data.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="领用人员工不存在")
    if employee.status != "在职":
        raise HTTPException(status_code=400, detail=f"员工「{employee.name}」已离职，无法领用")
    try:
        asset.status = "已领用"
        asset.user_id = employee.id
        db.add(
            AssetRecord(
                asset_id=asset.id,
                employee_id=employee.id,
                action="领用",
                operator_id=admin.id,
                remark=data.remark,
            )
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="领用失败，数据已回滚，请重试")
    db.refresh(asset)
    log_operation(admin, "资产领用", f"{asset.asset_no} {asset.name} -> {employee.name}")
    return success(AssetOut.model_validate(asset), msg=f"「{asset.name}」领用成功")


@router.post("/{asset_id}/return", summary="资产归还")
def return_asset(
    asset_id: int,
    data: ReturnRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    if asset.status != "已领用":
        raise HTTPException(status_code=400, detail=f"该资产当前状态为「{asset.status}」，无需归还")
    if not asset.user_id:
        raise HTTPException(status_code=400, detail="该资产没有领用记录，无法归还")
    try:
        db.add(
            AssetRecord(
                asset_id=asset.id,
                employee_id=asset.user_id,
                action="归还",
                operator_id=admin.id,
                remark=data.remark,
            )
        )
        asset.status = "空闲"
        asset.user_id = None
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="归还失败，数据已回滚，请重试")
    db.refresh(asset)
    log_operation(admin, "资产归还", f"{asset.asset_no} {asset.name}")
    return success(AssetOut.model_validate(asset), msg=f"「{asset.name}」归还成功")
