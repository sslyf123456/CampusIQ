"""会话管理端点 — GET/POST/DELETE /api/ai/conversations"""

import logging
from typing import List, Optional

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.chat import (
    ConversationResponse,
    ConversationDetailResponse,
    CreateConversationRequest,
)
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["conversations"])

conversation_service = ConversationService()


def extract_user_from_token(authorization: Optional[str] = Header(None)) -> dict:
    """从 Authorization header 中解析 JWT，获取用户信息。

    Args:
        authorization: HTTP Authorization header 值

    Returns:
        dict: 包含 sub(学号)、role(角色)、db_id(数据库主键) 的用户信息

    Raises:
        HTTPException: JWT 缺失或无效时抛出 401 错误
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少 Authorization header")

    token_parts = authorization.split(" ")
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization header 格式无效")

    token = token_parts[1]

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return {
            "sub": payload.get("sub", ""),
            "role": payload.get("role", "student"),
            "db_id": payload.get("db_id", 0),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="JWT 已过期")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"JWT 无效: {str(e)}")


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """获取当前用户会话列表。

    Args:
        db: 数据库会话
        authorization: JWT Authorization header

    Returns:
        List[ConversationResponse]: 用户会话列表
    """
    user_info = extract_user_from_token(authorization)
    student_id = user_info["sub"]  # 使用学号作为 student_id
    conversations = conversation_service.get_conversations(db, student_id)
    return conversations


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """创建新会话。

    Args:
        request: 创建会话请求（title）
        db: 数据库会话
        authorization: JWT Authorization header

    Returns:
        ConversationResponse: 新创建的会话
    """
    user_info = extract_user_from_token(authorization)
    student_id = user_info["sub"]  # 使用学号作为 student_id
    conversation = conversation_service.create_conversation(db, student_id, request.title)
    return conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """获取会话详情（含消息列表）。

    Args:
        conversation_id: 会话ID
        db: 数据库会话
        authorization: JWT Authorization header

    Returns:
        ConversationDetailResponse: 会话详情及消息列表
    """
    user_info = extract_user_from_token(authorization)
    student_id = user_info["sub"]  # 使用学号作为 student_id
    conversation = conversation_service.get_conversation(db, conversation_id, student_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在或不属于当前用户")
    return conversation


@router.delete("/conversations/{conversation_id}")
async def close_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """关闭会话（设置 status=closed）。

    Args:
        conversation_id: 会话ID
        db: 数据库会话
        authorization: JWT Authorization header

    Returns:
        dict: 操作结果
    """
    user_info = extract_user_from_token(authorization)
    student_id = user_info["sub"]  # 使用学号作为 student_id
    conversation = conversation_service.close_conversation(db, conversation_id, student_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在或不属于当前用户")
    return {"message": "会话已关闭", "conversation_id": conversation_id}
