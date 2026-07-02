"""对话请求/响应、SSE 事件类型 — Pydantic Schema 定义。"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    """对话请求 Schema。"""

    conversation_id: Optional[int] = Field(None, description="会话ID，为空则自动创建新会话")
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息内容")


class IntentResult(BaseModel):
    """意图识别结果 Schema。"""

    intent: str = Field(..., description="识别到的意图类别")
    confidence: float = Field(..., ge=0.0, le=1.0, description="意图置信度")
    clarify_question: Optional[str] = Field(None, description="模糊意图时的反问建议")
    keyword: Optional[str] = Field(None, description="提取的关键词（如通知检索关键词）")


class SSEEvent(BaseModel):
    """SSE 事件数据 Schema（与架构师设计统一）。

    event 类型包括：
    - thinking: 思考中/处理进行中提示，data = {"content": "...", "clarify": bool}
    - agent_call: Sub-Agent 开始处理，data = {"agent": "schedule", "description": "..."}
    - result: 最终回答（流式逐字输出），data = {"content": "...", "agent": "schedule"}
    - error: 错误信息，data = {"message": "...", "fallback": bool}
    - done: 流结束标记，data = {}
    - clarify: 反问澄清，data = {"question": "..."}
    """

    event: str = Field(..., description="事件类型")
    data: str = Field(..., description="事件数据（JSON 字符串或纯文本）")


class ConversationResponse(BaseModel):
    """会话列表/详情响应 Schema。"""

    id: int = Field(..., description="会话ID")
    student_id: str = Field(..., description="学号")
    title: str = Field(..., description="会话标题")
    status: str = Field(..., description="会话状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ConversationDetailResponse(BaseModel):
    """会话详情响应（含消息列表）Schema。"""

    id: int = Field(..., description="会话ID")
    student_id: str = Field(..., description="学号")
    title: str = Field(..., description="会话标题")
    status: str = Field(..., description="会话状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    messages: List["MessageResponse"] = Field(default_factory=list, description="消息列表")


class MessageResponse(BaseModel):
    """消息响应 Schema。"""

    id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="所属会话ID")
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    agent_name: Optional[str] = Field(None, description="处理该消息的 Agent 名称")
    metadata_: Optional[Any] = Field(None, description="附加元数据")
    created_at: datetime = Field(..., description="创建时间")


class CreateConversationRequest(BaseModel):
    """创建新会话请求 Schema。"""

    title: str = Field(default="新对话", max_length=200, description="会话标题")


# 解决 forward reference
ConversationDetailResponse.model_rebuild()
