from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RepairOrderCreate(BaseModel):
    description: str = Field(..., min_length=1)
    location: Optional[str] = Field(None, max_length=128)
    contact_phone: Optional[str] = Field(None, max_length=32)


class RepairOrderUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(pending|processing|completed)$")
    handler: Optional[str] = Field(None, max_length=64)
    handle_note: Optional[str] = None


class RepairOrderOut(BaseModel):
    id: int
    student_id: int
    description: str
    location: Optional[str]
    contact_phone: Optional[str]
    status: str
    handler: Optional[str]
    handle_note: Optional[str]
    submitted_at: datetime
    processed_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
