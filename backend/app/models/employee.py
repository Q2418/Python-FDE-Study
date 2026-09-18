from sqlalchemy import Column, Date, DateTime, Integer, String, func

from ..database import Base


class Employee(Base):
    """员工表"""

    __tablename__ = "employee"
    __table_args__ = {"comment": "员工表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    emp_no = Column(String(32), unique=True, nullable=False, comment="工号")
    name = Column(String(50), nullable=False, comment="姓名")
    gender = Column(String(10), default="男", comment="性别")
    department = Column(String(50), comment="部门")
    position = Column(String(50), comment="职位")
    phone = Column(String(20), comment="手机号")
    email = Column(String(100), comment="邮箱")
    hire_date = Column(Date, comment="入职日期")
    status = Column(String(10), default="在职", comment="状态：在职/离职")
    attachment_path = Column(String(255), comment="附件存储路径")
    attachment_name = Column(String(255), comment="附件原始文件名")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
