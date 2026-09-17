from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, func

from ..database import Base


class Asset(Base):
    """资产表"""

    __tablename__ = "asset"
    __table_args__ = {"comment": "资产表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    asset_no = Column(String(32), unique=True, nullable=False, comment="资产编号")
    name = Column(String(100), nullable=False, comment="资产名称")
    category = Column(String(50), comment="资产类别")
    brand = Column(String(50), comment="品牌")
    model = Column(String(50), comment="型号")
    price = Column(Numeric(10, 2), default=0, comment="购置价格")
    purchase_date = Column(Date, comment="购置日期")
    status = Column(String(10), default="空闲", comment="状态：空闲/已领用/维修/报废")
    user_id = Column(Integer, comment="领用人员工ID（关联employee.id）")
    remark = Column(String(255), comment="备注")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
