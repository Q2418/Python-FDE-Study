from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AssetBase(BaseModel):
    asset_no: str = Field(..., min_length=1, max_length=32, pattern=r"^[A-Za-z0-9\-_]+$", description="资产编号")
    name: str = Field(..., min_length=1, max_length=100, description="资产名称")
    category: Optional[str] = Field(None, max_length=50, description="资产类别")
    brand: Optional[str] = Field(None, max_length=50, description="品牌")
    model: Optional[str] = Field(None, max_length=50, description="型号")
    price: Optional[float] = Field(0.0, ge=0, le=99999999.99, description="购置价格")
    purchase_date: Optional[date] = Field(None, description="购置日期")
    status: Optional[Literal["空闲", "已领用", "维修", "报废"]] = Field("空闲", description="状态：空闲/已领用/维修/报废")
    user_id: Optional[int] = Field(None, ge=1, description="领用人员工ID")
    remark: Optional[str] = Field(None, max_length=255, description="备注")

    @field_validator("category", "brand", "model", "remark", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return None if v == "" else v

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
    asset_no: Optional[str] = Field(None, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9\-_]+$", description="资产编号")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="资产名称")
    category: Optional[str] = Field(None, max_length=50, description="资产类别")
    brand: Optional[str] = Field(None, max_length=50, description="品牌")
    model: Optional[str] = Field(None, max_length=50, description="型号")
    price: Optional[float] = Field(None, ge=0, le=99999999.99, description="购置价格")
    purchase_date: Optional[date] = Field(None, description="购置日期")
    status: Optional[Literal["空闲", "已领用", "维修", "报废"]] = Field(None, description="状态")
    user_id: Optional[int] = Field(None, ge=1, description="领用人员工ID")
    remark: Optional[str] = Field(None, max_length=255, description="备注")

    @field_validator("category", "brand", "model", "remark", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return None if v == "" else v

    @field_validator("user_id", mode="before")
    @classmethod
    def empty_user_id_to_none(cls, v):
        return None if v == "" else v

    @field_validator("price", mode="before")
    @classmethod
    def empty_price_to_none(cls, v):
        return None if v == "" else v


class AssetListOut(BaseModel):
    id: int
    asset_no: str
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    price: Optional[float] = None
    purchase_date: Optional[date] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
    remark: Optional[str] = None

    model_config = {"from_attributes": True}


class AssetOut(AssetBase):
    id: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
