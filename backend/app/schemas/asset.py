from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AssetBase(BaseModel):
    asset_no: str = Field(..., max_length=32, description="资产编号")
    name: str = Field(..., max_length=100, description="资产名称")
    category: Optional[str] = Field(None, max_length=50, description="资产类别")
    brand: Optional[str] = Field(None, max_length=50, description="品牌")
    model: Optional[str] = Field(None, max_length=50, description="型号")
    price: Optional[float] = Field(0.0, ge=0, description="购置价格")
    purchase_date: Optional[date] = Field(None, description="购置日期")
    status: Optional[str] = Field("空闲", max_length=10, description="状态：空闲/已领用/维修/报废")
    user_id: Optional[int] = Field(None, description="领用人员工ID")
    remark: Optional[str] = Field(None, max_length=255, description="备注")

    @field_validator("user_id", mode="before")
    @classmethod
    def empty_user_id_to_none(cls, v):
        return None if v == "" else v

    @field_validator("price", mode="before")
    @classmethod
    def empty_price_to_zero(cls, v):
        return 0.0 if v in ("", None) else v


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    asset_no: Optional[str] = Field(None, max_length=32, description="资产编号")
    name: Optional[str] = Field(None, max_length=100, description="资产名称")
    category: Optional[str] = Field(None, max_length=50, description="资产类别")
    brand: Optional[str] = Field(None, max_length=50, description="品牌")
    model: Optional[str] = Field(None, max_length=50, description="型号")
    price: Optional[float] = Field(None, ge=0, description="购置价格")
    purchase_date: Optional[date] = Field(None, description="购置日期")
    status: Optional[str] = Field(None, max_length=10, description="状态")
    user_id: Optional[int] = Field(None, description="领用人员工ID")
    remark: Optional[str] = Field(None, max_length=255, description="备注")

    @field_validator("user_id", mode="before")
    @classmethod
    def empty_user_id_to_none(cls, v):
        return None if v == "" else v

    @field_validator("price", mode="before")
    @classmethod
    def empty_price_to_zero(cls, v):
        return None if v == "" else v


class AssetOut(AssetBase):
    id: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
