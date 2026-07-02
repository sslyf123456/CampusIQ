"""会话 CRUD 服务 — 管理对话会话的创建、查询、关闭和消息存储。"""

import logging
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ConversationResponse, ConversationDetailResponse, MessageResponse

logger = logging.getLogger(__name__)


class ConversationService:
    """会话管理服务，处理对话会话的 CRUD 操作。"""

    def create_conversation(self, db: Session, student_id: int, title: str = "新对话") -> ConversationResponse:
        """创建新会话。

        Args:
            db: 数据库会话
            student_id: 学生数据库主键ID（从 JWT 的 db_id 获取）
            title: 会话标题

        Returns:
            ConversationResponse: 新创建的会话信息
        """
        conversation = Conversation(
            student_id=student_id,
            title=title,
            status="active",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        logger.info(f"创建会话: id={conversation.id}, student_id={student_id}")
        return ConversationResponse(
            id=conversation.id,
            student_id=conversation.student_id,
            title=conversation.title,
            status=conversation.status,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    def get_conversations(self, db: Session, student_id: int) -> List[ConversationResponse]:
        """获取用户会话列表（仅返回 active 状态的会话）。

        Args:
            db: 数据库会话
            student_id: 学生数据库主键ID

        Returns:
            List[ConversationResponse]: 用户会话列表
        """
        conversations = db.query(Conversation).filter(
            Conversation.student_id == student_id,
            Conversation.status == "active",
        ).order_by(Conversation.updated_at.desc()).all()
        return [
            ConversationResponse(
                id=c.id,
                student_id=c.student_id,
                title=c.title,
                status=c.status,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in conversations
        ]

    def get_conversation(self, db: Session, conversation_id: int, student_id: int) -> Optional[ConversationDetailResponse]:
        """获取会话详情（含消息列表），需验证会话归属。

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            student_id: 学生数据库主键ID（用于验证归属）

        Returns:
            Optional[ConversationDetailResponse]: 会话详情，不存在或不属于当前用户返回 None
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.student_id == student_id,
        ).first()

        if not conversation:
            return None

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
        ).order_by(Message.created_at.asc()).all()

        return ConversationDetailResponse(
            id=conversation.id,
            student_id=conversation.student_id,
            title=conversation.title,
            status=conversation.status,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[
                MessageResponse(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    agent_name=m.agent_name,
                    metadata_=m.metadata_,
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )

    def close_conversation(self, db: Session, conversation_id: int, student_id: int) -> Optional[Conversation]:
        """关闭会话（设置 status=closed）。

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            student_id: 学生数据库主键ID（用于验证归属）

        Returns:
            Optional[Conversation]: 关闭的会话对象，不存在或不属于当前用户返回 None
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.student_id == student_id,
        ).first()

        if not conversation:
            return None

        conversation.status = "closed"
        db.commit()
        db.refresh(conversation)
        logger.info(f"关闭会话: id={conversation_id}")
        return conversation

    def add_message(
        self,
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """添加消息到会话。

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            role: 消息角色（user/assistant/system）
            content: 消息内容
            agent_name: 产生该消息的 Agent 名称（可选）
            metadata: 附加元数据（可选）

        Returns:
            Message: 新创建的消息对象
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_name=agent_name,
            metadata_=metadata,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def get_messages(self, db: Session, conversation_id: int, limit: int = 20) -> List[Message]:
        """获取会话消息列表（最近 N 条）。

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            limit: 返回的消息条数上限

        Returns:
            List[Message]: 消息列表
        """
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
        ).order_by(Message.created_at.desc()).limit(limit).all()
        # 按时间正序返回（最旧的在前）
        return list(reversed(messages))
