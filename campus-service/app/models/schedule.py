from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base

student_schedule = Table(
    "student_schedule",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("campus.students.id", ondelete="CASCADE"), primary_key=True),
    Column("schedule_id", Integer, ForeignKey("campus.schedules.id", ondelete="CASCADE"), primary_key=True),
    schema="campus",
)


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = {"schema": "campus"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_name = Column(String(128), nullable=False)
    teacher = Column(String(64))
    weekday = Column(Integer, nullable=False)
    start_period = Column(Integer, nullable=False)
    end_period = Column(Integer, nullable=False)
    location = Column(String(128))
    start_week = Column(Integer, nullable=False, default=1)
    end_week = Column(Integer, nullable=False, default=16)
    semester = Column(String(32), nullable=False, default="2025-2026-2")
    created_by = Column(Integer, ForeignKey("campus.admins.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    students = relationship(
        "Student",
        secondary="campus.student_schedule",
        back_populates="schedules",
        lazy="selectin",
    )


from .student import Student  # noqa: E402

Student.schedules = relationship(
    "Schedule",
    secondary="campus.student_schedule",
    back_populates="students",
    lazy="selectin",
)
