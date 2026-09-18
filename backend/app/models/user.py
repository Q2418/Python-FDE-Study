from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import relationship

from ..database import Base

user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True, comment="用户ID"),
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True, comment="角色ID"),
    comment="用户角色关联表",
)


class Role(Base):
    """角色表"""

    __tablename__ = "role"
    __table_args__ = {"comment": "角色表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    code = Column(String(32), unique=True, nullable=False, comment="角色编码：admin/employee")
    name = Column(String(50), nullable=False, comment="角色名称")
    description = Column(String(255), comment="描述")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")


class User(Base):
    """用户表"""

    __tablename__ = "user"
    __table_args__ = {"comment": "用户表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    username = Column(String(50), unique=True, nullable=False, comment="登录账号")
    password_hash = Column(String(100), nullable=False, comment="密码哈希")
    real_name = Column(String(50), comment="姓名")
    status = Column(String(10), default="启用", comment="状态：启用/禁用")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    roles = relationship("Role", secondary=user_role, lazy="selectin")

    def has_role(self, code: str) -> bool:
        return any(role.code == code for role in self.roles)
