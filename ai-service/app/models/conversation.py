"""会话表模型 — 映射 ai_campus.conversations 表。"""

from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class Conversation(Base):
    """会话模型，存储用户对话会话信息。"""

    __tablename__ = "conversations"
    __table_args__ = {"schema": "ai_campus"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="会话ID")
    student_id = Column(Integer, nullable=False, index=True, comment="学生数据库ID")
    title = Column(String(200), nullable=False, default="新对话", comment="会话标题")
    status = Column(String(20), nullable=False, default="active", comment="会话状态: active/closed")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, student_id='{self.student_id}', title='{self.title}', status='{self.status}')>"
