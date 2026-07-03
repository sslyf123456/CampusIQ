from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func

from ..database import Base


class Notice(Base):
    __tablename__ = "notices"
    __table_args__ = {"schema": "campus"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, default="general")
    publisher = Column(String(64))
    published_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, onupdate=func.now())
    created_by = Column(Integer, ForeignKey("campus.admins.id", ondelete="SET NULL"))
