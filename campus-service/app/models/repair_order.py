from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func

from ..database import Base


class RepairOrder(Base):
    __tablename__ = "repair_orders"
    __table_args__ = {"schema": "campus"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("campus.students.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(128))
    contact_phone = Column(String(32))
    status = Column(String(32), nullable=False, default="pending")
    handler = Column(String(64))
    handle_note = Column(Text)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
