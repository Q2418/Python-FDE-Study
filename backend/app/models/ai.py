from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from ..database import Base


class AiDocument(Base):
    """AI 知识库文档表"""

    __tablename__ = "ai_document"
    __table_args__ = {"comment": "AI知识库文档表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(255), nullable=False, comment="存储路径")
    file_size = Column(Integer, default=0, comment="文件大小(字节)")
    chunk_count = Column(Integer, default=0, comment="切片数量")
    category = Column(String(20), default="upload", comment="来源：upload 上传 / project 项目资料")
    uploader_id = Column(Integer, ForeignKey("user.id"), comment="上传人用户ID")
    create_time = Column(DateTime, server_default=func.now(), comment="上传时间")


class AiChunk(Base):
    """AI 知识库文档切片表"""

    __tablename__ = "ai_chunk"
    __table_args__ = {"comment": "AI知识库切片表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    document_id = Column(Integer, ForeignKey("ai_document.id"), nullable=False, comment="文档ID")
    seq = Column(Integer, default=0, comment="切片序号")
    content = Column(Text, nullable=False, comment="切片内容")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")


class AiWorkflowRun(Base):
    """AI Agent 工作流运行记录表"""

    __tablename__ = "ai_workflow_run"
    __table_args__ = {"comment": "AI工作流运行记录表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    requirement = Column(Text, nullable=False, comment="开发需求")
    status = Column(String(20), default="成功", comment="状态：成功/失败")
    review_rounds = Column(Integer, default=0, comment="评审循环轮次")
    steps = Column(Text, comment="步骤日志(JSON)")
    result = Column(Text, comment="最终产出代码")
    duration_ms = Column(Integer, default=0, comment="总耗时(毫秒)")
    operator_id = Column(Integer, ForeignKey("user.id"), comment="操作人用户ID")
    create_time = Column(DateTime, server_default=func.now(), comment="运行时间")
