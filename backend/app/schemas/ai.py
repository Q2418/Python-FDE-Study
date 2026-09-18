from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="问题内容")
    top_k: int = Field(3, ge=1, le=10, description="检索条数")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="自然语言问题")


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_size: Optional[int] = 0
    chunk_count: Optional[int] = 0
    create_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
