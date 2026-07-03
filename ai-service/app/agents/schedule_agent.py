"""课表查询 Agent — 接收课表数据，结合用户问题生成回答。"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)

SCHEDULE_PROMPT_TEMPLATE = """你是一个校园课表查询助手。根据以下课表数据，回答用户的问题。

课表数据：
{schedule_data}

用户问题：{user_question}

对话历史（最近消息）：
{history_context}

请根据课表数据给出清晰、准确的回答。如果课表数据为空或无法匹配用户问题，请告知用户暂无课表信息。
回答时请按时间顺序整理课程信息，包括课程名称、上课时间、教室、教师等。
注意：回答中不要使用任何emoji表情符号，用纯文字即可。"""


class ScheduleAgent:
    """课表查询 Agent，处理与课程安排相关的用户问题。"""

    def __init__(self) -> None:
        """初始化 ScheduleAgent，创建 LLM 客户端。"""
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL_NAME
        self.name = "ScheduleAgent"

    async def run(self, query: str, history_context: str = "", **kwargs) -> str:
        """处理课表查询请求。

        Args:
            query: 用户原始问题
            history_context: 对话历史上下文（可选），用于理解上下文关联的提问
            **kwargs: 包含 schedule_data 的关键字参数

        Returns:
            str: Agent 处理结果摘要

        Raises:
            LLMError: LLM 调用异常时抛出
        """
        schedule_data = kwargs.get("schedule_data")
        if schedule_data is None:
            return "课表数据获取失败，无法为您查询课程安排。请稍后再试或联系教务处。"

        schedule_str = json.dumps(schedule_data, ensure_ascii=False, indent=2)
        prompt = SCHEDULE_PROMPT_TEMPLATE.format(
            schedule_data=schedule_str,
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
            logger.info(f"ScheduleAgent 处理完成, 问题: {query[:50]}...")
            return result
        except Exception as e:
            logger.error(f"ScheduleAgent LLM 调用异常: {e}", exc_info=True)
            raise LLMError(f"课表查询处理失败: {str(e)}") from e
