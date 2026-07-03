"""宿舍报修查询 Agent — 接收报修数据，结合用户问题生成回答。"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)

REPAIR_PROMPT_TEMPLATE = """你是一个校园宿舍报修查询助手。根据以下报修数据，回答用户的问题。

报修数据：
{repair_data}

用户问题：{user_question}

对话历史（最近消息）：
{history_context}

请根据报修数据给出清晰、准确的回答。如果报修数据为空，请告知用户暂无报修记录。
回答时请整理报修信息，包括报修类型、提交时间、当前状态等。
注意：回答中不要使用任何emoji表情符号，用纯文字即可。"""


class RepairAgent:
    """宿舍报修查询 Agent，处理与宿舍报修相关的用户问题。"""

    def __init__(self) -> None:
        """初始化 RepairAgent，创建 LLM 客户端。"""
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL_NAME
        self.name = "RepairAgent"

    async def run(self, query: str, history_context: str = "", **kwargs) -> str:
        """处理报修查询请求。

        Args:
            query: 用户原始问题
            history_context: 对话历史上下文（可选），用于理解上下文关联的提问
            **kwargs: 包含 repair_data 的关键字参数

        Returns:
            str: Agent 处理结果摘要

        Raises:
            LLMError: LLM 调用异常时抛出
        """
        repair_data = kwargs.get("repair_data")
        if repair_data is None:
            return "报修数据获取失败，无法为您查询报修进度。请稍后再试或联系宿管办。"

        repair_str = json.dumps(repair_data, ensure_ascii=False, indent=2)
        prompt = REPAIR_PROMPT_TEMPLATE.format(
            repair_data=repair_str,
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
            logger.info(f"RepairAgent 处理完成, 问题: {query[:50]}...")
            return result
        except Exception as e:
            logger.error(f"RepairAgent LLM 调用异常: {e}", exc_info=True)
            raise LLMError(f"报修查询处理失败: {str(e)}") from e
