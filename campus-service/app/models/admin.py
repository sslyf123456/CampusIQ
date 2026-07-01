from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from ..database import Base


class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = {"schema": "campus"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(128))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
