from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BorrowRequest(BaseModel):
    employee_id: int = Field(..., ge=1, description="领用人员工ID")
    remark: Optional[str] = Field(None, max_length=255, description="备注")

    @field_validator("remark", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return None if v == "" else v


class ReturnRequest(BaseModel):
    remark: Optional[str] = Field(None, max_length=255, description="备注")

    @field_validator("remark", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return None if v == "" else v


class RecordOut(BaseModel):
    id: int
    asset_id: int
    asset_no: str
    asset_name: str
    employee_id: int
    employee_name: Optional[str] = None
    action: str
    operator_name: Optional[str] = None
    remark: Optional[str] = None
    create_time: Optional[datetime] = None
