from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func

from ..database import Base


class ScholarshipRecord(Base):
    __tablename__ = "scholarship_records"
    __table_args__ = {"schema": "campus"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("campus.students.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    amount = Column(Numeric(10, 2))
    status = Column(String(32), nullable=False, default="pending")
    semester = Column(String(32), nullable=False, default="2025-2026-2")
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
