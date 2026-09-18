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
