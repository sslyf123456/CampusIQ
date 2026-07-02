"""SSE 事件构造与推送模块。"""

import json
from typing import Any, Dict, Optional

from app.schemas.chat import SSEEvent


def format_sse_event(event_type: str, data: str) -> str:
    """构造 SSE 格式的事件数据。

    SSE 标准格式为：
    event: {type}
    data: {data}

    最后以两个换行符结束，表示事件发送完毕。

    Args:
        event_type: 事件类型（thinking/agent_call/result/error/done/clarify）
        data: 事件数据（JSON 字符串或纯文本）

    Returns:
        str: SSE 格式的事件字符串
    """
    return f"event: {event_type}\ndata: {data}\n\n"


def format_sse_json_event(event_type: str, data_dict: Dict[str, Any]) -> str:
    """构造 SSE 格式的事件数据（自动将字典转为 JSON）。

    Args:
        event_type: 事件类型
        data_dict: 事件数据字典

    Returns:
        str: SSE 格式的事件字符串
    """
    data_json = json.dumps(data_dict, ensure_ascii=False)
    return format_sse_event(event_type, data_json)


def create_sse_event(event_type: str, data: str) -> SSEEvent:
    """创建 SSEEvent 对象。

    Args:
        event_type: 事件类型
        data: 事件数据

    Returns:
        SSEEvent: SSE 事件对象
    """
    return SSEEvent(event=event_type, data=data)


def create_sse_json_event(event_type: str, data_dict: Dict[str, Any]) -> SSEEvent:
    """创建 SSEEvent 对象（自动将字典转为 JSON）。

    Args:
        event_type: 事件类型
        data_dict: 事件数据字典

    Returns:
        SSEEvent: SSE 事件对象
    """
    data_json = json.dumps(data_dict, ensure_ascii=False)
    return SSEEvent(event=event_type, data=data_json)
