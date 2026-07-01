from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NoticeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: str = Field("general", pattern=r"^(academic|dormitory|scholarship|general)$")
    publisher: Optional[str] = Field(None, max_length=64)


class NoticeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, pattern=r"^(academic|dormitory|scholarship|general)$")
    publisher: Optional[str] = Field(None, max_length=64)


class NoticeOut(BaseModel):
    id: int
    title: str
    content: str
    category: str
    publisher: Optional[str]
    published_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True
