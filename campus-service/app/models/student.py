from sqlalchemy import Column, Integer, String, Date, DateTime, CheckConstraint
from sqlalchemy.sql import func

from ..database import Base


class Student(Base):
    __tablename__ = "students"
    __table_args__ = {"schema": "campus"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(32), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    password_hash = Column(String(255), nullable=False)
    gender = Column(String(8))
    department = Column(String(128))
    major = Column(String(128))
    phone = Column(String(20))
    email = Column(String(128))
    birth_date = Column(Date)
    enrollment_year = Column(Integer)
    dorm_building = Column(String(32))
    dorm_room = Column(String(16))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
