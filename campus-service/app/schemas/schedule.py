from typing import Optional, List

from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    course_name: str = Field(..., min_length=1, max_length=128)
    teacher: Optional[str] = Field(None, max_length=64)
    weekday: int = Field(..., ge=1, le=7)
    start_period: int = Field(..., ge=1, le=12)
    end_period: int = Field(..., ge=1, le=12)
    location: Optional[str] = Field(None, max_length=128)
    start_week: int = Field(1, ge=1, le=20)
    end_week: int = Field(16, ge=1, le=20)
    semester: str = Field("2025-2026-2", max_length=32)


class ScheduleUpdate(BaseModel):
    course_name: Optional[str] = Field(None, min_length=1, max_length=128)
    teacher: Optional[str] = Field(None, max_length=64)
    weekday: Optional[int] = Field(None, ge=1, le=7)
    start_period: Optional[int] = Field(None, ge=1, le=12)
    end_period: Optional[int] = Field(None, ge=1, le=12)
    location: Optional[str] = Field(None, max_length=128)
    start_week: Optional[int] = Field(None, ge=1, le=20)
    end_week: Optional[int] = Field(None, ge=1, le=20)
    semester: Optional[str] = Field(None, max_length=32)


class ScheduleOut(BaseModel):
    id: int
    course_name: str
    teacher: Optional[str]
    weekday: int
    start_period: int
    end_period: int
    location: Optional[str]
    start_week: int
    end_week: int
    semester: str

    class Config:
        from_attributes = True


class AddStudentsRequest(BaseModel):
    student_ids: List[str]
