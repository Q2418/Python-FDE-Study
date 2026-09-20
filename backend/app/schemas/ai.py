from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="问题内容")
    top_k: int = Field(3, ge=1, le=10, description="检索条数")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="自然语言问题")


class WorkflowRequest(BaseModel):
    requirement: str = Field(..., min_length=2, max_length=500, description="开发需求")


class SkillRunRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="技能名称")
    arguments: dict = Field(default_factory=dict, description="技能参数")


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_size: Optional[int] = 0
    chunk_count: Optional[int] = 0
    create_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
