from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, load_only

from ..core.response import success
from ..database import get_db
from ..models.asset import Asset
from ..schemas.asset import AssetCreate, AssetListOut, AssetOut, AssetUpdate

router = APIRouter(prefix="/api/asset", tags=["资产管理"])

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


@router.get("/list", summary="分页查询资产列表")
def list_assets(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    name: str = Query("", description="资产名称（模糊查询）"),
    status: str = Query("", description="状态（精准查询）"),
    db: Session = Depends(get_db),
):
    query = db.query(Asset).options(load_only(*LIST_FIELDS))
    if name:
        query = query.filter(Asset.name.like(f"%{name}%"))
    if status:
        query = query.filter(Asset.status == status)
    total = query.count()
    items = query.order_by(Asset.id.desc()).offset((page - 1) * size).limit(size).all()
    return success({"total": total, "items": [AssetListOut.model_validate(item) for item in items]})


@router.get("/{asset_id}", summary="查询单个资产")
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    return success(AssetOut.model_validate(asset))


@router.post("", summary="新增资产")
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    check_asset_conflict(db, data.asset_no, data.name)
    asset = Asset(**data.model_dump())
    db.add(asset)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="资产编号已存在，请更换后重试")
    db.refresh(asset)
    return success(AssetOut.model_validate(asset), msg="新增成功")


@router.put("/{asset_id}", summary="修改资产")
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)):
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
    return success(AssetOut.model_validate(asset), msg="修改成功")


@router.delete("/{asset_id}", summary="删除资产")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    db.delete(asset)
    db.commit()
    return success(msg="删除成功")
