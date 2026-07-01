from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from ..database import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    __table_args__ = {"schema": "campus"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    user_sub = Column(String(64), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
