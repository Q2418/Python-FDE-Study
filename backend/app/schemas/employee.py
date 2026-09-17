from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class EmployeeBase(BaseModel):
    emp_no: str = Field(..., max_length=32, description="工号")
    name: str = Field(..., max_length=50, description="姓名")
    gender: Optional[str] = Field("男", max_length=10, description="性别")
    department: Optional[str] = Field(None, max_length=50, description="部门")
    position: Optional[str] = Field(None, max_length=50, description="职位")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    hire_date: Optional[date] = Field(None, description="入职日期")
    status: Optional[str] = Field("在职", max_length=10, description="状态：在职/离职")


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    emp_no: Optional[str] = Field(None, max_length=32, description="工号")
    name: Optional[str] = Field(None, max_length=50, description="姓名")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    department: Optional[str] = Field(None, max_length=50, description="部门")
    position: Optional[str] = Field(None, max_length=50, description="职位")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    hire_date: Optional[date] = Field(None, description="入职日期")
    status: Optional[str] = Field(None, max_length=10, description="状态：在职/离职")


class EmployeeOut(EmployeeBase):
    id: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
