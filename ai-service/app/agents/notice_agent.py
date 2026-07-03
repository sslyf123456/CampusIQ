"""通知检索 Agent — 接收通知数据，结合用户问题生成回答。"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)

NOTICE_PROMPT_TEMPLATE = """你是一个校园通知检索助手。根据以下通知数据，回答用户的问题。

通知数据：
{notice_data}

用户问题：{user_question}

对话历史（最近消息）：
{history_context}

请根据通知数据给出清晰、准确的回答。如果通知数据为空，请告知用户暂无相关通知。
回答时请整理通知信息，包括通知标题、发布时间、主要内容摘要等。如果有多条相关通知，请逐条列出。
注意：回答中不要使用任何emoji表情符号，用纯文字即可。"""


class NoticeAgent:
    """通知检索 Agent，处理与校园通知公告相关的用户问题。"""

    def __init__(self) -> None:
        """初始化 NoticeAgent，创建 LLM 客户端。"""
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL_NAME
        self.name = "NoticeAgent"

    async def run(self, query: str, history_context: str = "", **kwargs) -> str:
        """处理通知检索请求。

        Args:
            query: 用户原始问题
            history_context: 对话历史上下文（可选），用于理解上下文关联的提问
            **kwargs: 包含 notice_data 的关键字参数

        Returns:
            str: Agent 处理结果摘要

        Raises:
            LLMError: LLM 调用异常时抛出
        """
        notice_data = kwargs.get("notice_data")
        if notice_data is None:
            return "通知数据获取失败，无法为您检索通知信息。请稍后再试或查看学校官网。"

        notice_str = json.dumps(notice_data, ensure_ascii=False, indent=2)
        prompt = NOTICE_PROMPT_TEMPLATE.format(
            notice_data=notice_str,
            user_question=query,
            history_context=history_context or "（无历史消息）",
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )
            result = response.choices[0].message.content or ""
            logger.info(f"NoticeAgent 处理完成, 问题: {query[:50]}...")
            return result
        except Exception as e:
            logger.error(f"NoticeAgent LLM 调用异常: {e}", exc_info=True)
            raise LLMError(f"通知检索处理失败: {str(e)}") from e
