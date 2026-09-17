from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.asset import Asset
from ..schemas.asset import AssetCreate, AssetOut, AssetUpdate

router = APIRouter(prefix="/api/asset", tags=["资产管理"])


@router.get("/list", summary="分页查询资产列表")
def list_assets(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    name: str = Query("", description="资产名称（模糊查询）"),
    status: str = Query("", description="状态（精准查询）"),
    db: Session = Depends(get_db),
):
    query = db.query(Asset)
    if name:
        query = query.filter(Asset.name.like(f"%{name}%"))
    if status:
        query = query.filter(Asset.status == status)
    total = query.count()
    items = query.order_by(Asset.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"total": total, "items": [AssetOut.model_validate(item) for item in items]}


@router.get("/{asset_id}", summary="查询单个资产")
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    return AssetOut.model_validate(asset)


@router.post("", summary="新增资产")
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    asset = Asset(**data.model_dump())
    db.add(asset)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="资产编号已存在，请更换后重试")
    db.refresh(asset)
    return AssetOut.model_validate(asset)


@router.put("/{asset_id}", summary="修改资产")
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="资产编号已存在，请更换后重试")
    db.refresh(asset)
    return AssetOut.model_validate(asset)


@router.delete("/{asset_id}", summary="删除资产")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    db.delete(asset)
    db.commit()
    return {"message": "删除成功"}
