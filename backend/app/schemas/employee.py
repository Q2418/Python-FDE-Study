from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmployeeBase(BaseModel):
    emp_no: str = Field(..., min_length=1, max_length=32, pattern=r"^[A-Za-z0-9\-_]+$", description="工号")
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    gender: Optional[Literal["男", "女"]] = Field("男", description="性别")
    department: Optional[str] = Field(None, max_length=50, description="部门")
    position: Optional[str] = Field(None, max_length=50, description="职位")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    hire_date: Optional[date] = Field(None, description="入职日期")
    status: Optional[Literal["在职", "离职"]] = Field("在职", description="状态：在职/离职")

    @field_validator("department", "position", "phone", "email", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return None if v == "" else v


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    emp_no: Optional[str] = Field(None, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9\-_]+$", description="工号")
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="姓名")
    gender: Optional[Literal["男", "女"]] = Field(None, description="性别")
    department: Optional[str] = Field(None, max_length=50, description="部门")
    position: Optional[str] = Field(None, max_length=50, description="职位")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    hire_date: Optional[date] = Field(None, description="入职日期")
    status: Optional[Literal["在职", "离职"]] = Field(None, description="状态：在职/离职")

    @field_validator("department", "position", "phone", "email", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return None if v == "" else v


class EmployeeListOut(BaseModel):
    id: int
    emp_no: str
    name: str
    gender: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[date] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class EmployeeOut(EmployeeBase):
    id: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
