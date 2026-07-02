from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ScholarshipCreate(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=32, description="学号")
    type: str = Field(..., max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    amount: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    status: str = Field("pending", pattern=r"^(pending|approved|rejected)$")
    semester: str = Field("2025-2026-2", max_length=32)
    note: Optional[str] = None


class ScholarshipUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=64)
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    amount: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    status: Optional[str] = Field(None, pattern=r"^(pending|approved|rejected)$")
    semester: Optional[str] = Field(None, max_length=32)
    note: Optional[str] = None


class ScholarshipOut(BaseModel):
    id: int
    student_id: int
    type: str
    name: str
    amount: Optional[Decimal]
    status: str
    semester: str
    note: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
