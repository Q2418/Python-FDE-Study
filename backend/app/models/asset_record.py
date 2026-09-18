from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from ..database import Base


class AssetRecord(Base):
    """资产领用记录表"""

    __tablename__ = "asset_record"
    __table_args__ = {"comment": "资产领用记录表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=False, comment="资产ID")
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False, comment="领用人员工ID")
    action = Column(String(10), nullable=False, comment="动作：领用/归还")
    operator_id = Column(Integer, ForeignKey("user.id"), comment="操作人用户ID")
    remark = Column(String(255), comment="备注")
    create_time = Column(DateTime, server_default=func.now(), comment="操作时间")
