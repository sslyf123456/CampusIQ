from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=64)
    gender: Optional[str] = Field(None, pattern=r"^(male|female)$")
    department: Optional[str] = Field(None, max_length=128)
    major: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=128)
    birth_date: Optional[date] = None
    enrollment_year: Optional[int] = None
    dorm_building: Optional[str] = Field(None, max_length=32)
    dorm_room: Optional[str] = Field(None, max_length=16)


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    gender: Optional[str] = Field(None, pattern=r"^(male|female)$")
    department: Optional[str] = Field(None, max_length=128)
    major: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=128)
    birth_date: Optional[date] = None
    enrollment_year: Optional[int] = None
    dorm_building: Optional[str] = Field(None, max_length=32)
    dorm_room: Optional[str] = Field(None, max_length=16)


class StudentOut(BaseModel):
    id: int
    student_id: str
    name: str
    gender: Optional[str]
    department: Optional[str]
    major: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    birth_date: Optional[date]
    enrollment_year: Optional[int]
    dorm_building: Optional[str]
    dorm_room: Optional[str]

    class Config:
        from_attributes = True
