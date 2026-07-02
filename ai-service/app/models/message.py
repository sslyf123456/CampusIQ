"""消息表模型 — 映射 ai_campus.messages 表。"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, JSON
from app.database import Base


class Message(Base):
    """消息模型，存储会话中的对话消息。"""

    __tablename__ = "messages"
    __table_args__ = {"schema": "ai_campus"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="消息ID")
    conversation_id = Column(
        Integer,
        ForeignKey("ai_campus.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属会话ID",
    )
    role = Column(String(20), nullable=False, comment="角色: user/assistant/system")
    content = Column(Text, nullable=False, comment="消息内容")
    agent_name = Column(String(50), nullable=True, comment="处理该消息的 Agent 名称")
    metadata_ = Column("metadata", JSON, nullable=True, comment="附加元数据(JSON)")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"
