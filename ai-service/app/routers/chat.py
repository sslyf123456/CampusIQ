"""SSE 流式对话端点 — POST /api/ai/chat"""

import json
import logging
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.database import get_db
from app.schemas.chat import ChatRequest, SSEEvent
from app.services.chat_service import ChatService
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["chat"])

chat_service = ChatService()


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

    # 提取 Bearer token
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


@router.post("/chat")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """SSE 流式对话端点。

    接收用户消息，通过 Master Agent 意图识别后路由到对应 Sub-Agent，
    最终通过 SSE 流式返回多个事件（thinking/agent_call/result/error/done/clarify）。

    Args:
        request: 对话请求（conversation_id + message）
        db: 数据库会话
        authorization: JWT Authorization header

    Returns:
        EventSourceResponse: SSE 流式响应
    """
    user_info = extract_user_from_token(authorization)
    db_id = user_info["db_id"]  # 使用数据库主键ID（与 conversations.student_id 一致）
    role = user_info["role"]  # 用户角色（student / admin）
    token = authorization.split(" ")[1] if authorization else ""

    async def event_generator():
        """SSE 事件异步生成器。"""
        try:
            async for sse_event in chat_service.stream_chat(
                db=db,
                token=token,
                student_db_id=db_id,
                role=role,
                conversation_id=request.conversation_id,
                user_message=request.message,
            ):
                # 直接 yield dict，sse_starlette 会自动序列化为标准 SSE 格式
                yield {"event": sse_event.event, "data": sse_event.data}
        except Exception as e:
            logger.error(f"SSE 流式对话异常: {e}", exc_info=True)
            error_data = json.dumps({"error": str(e)})
            yield {"event": "error", "data": error_data}

    return EventSourceResponse(event_generator())
