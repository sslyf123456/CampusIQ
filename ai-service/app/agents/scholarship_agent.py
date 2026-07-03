"""奖助学金查询 Agent — 接收奖助数据，结合用户问题生成回答。"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.prompts import get_system_prompt
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)

SCHOLARSHIP_PROMPT_TEMPLATE = """你是一个校园奖助学金查询助手。根据以下奖助学金数据，回答用户的问题。

奖助学金数据（JSON）：
{scholarship_data}

字段说明：
- type: 奖助类型（如奖学金、助学金等）
- name: 奖助名称
- amount: 金额（元）
- status: 审批状态（pending=待审批, approved=已通过, rejected=已驳回）
- semester: 所属学期（如2025-2026-2）
- note: 备注
- student_no / student_name: 学生学号和姓名
- created_at / updated_at: 创建和更新时间

用户问题：{user_question}

对话历史（最近消息）：
{history_context}

请严格根据奖助学金数据回答，不要编造数据中不存在的信息。如果数据为空，请告知用户暂无奖助学金信息。
回答时请整理奖助学金信息，包括名称、类型、金额、状态、学期等。
注意：回答中不要使用任何emoji表情符号，用纯文字即可。"""


class ScholarshipAgent:
    """奖助学金查询 Agent，处理与奖助学金相关的用户问题。"""

    def __init__(self) -> None:
        """初始化 ScholarshipAgent，创建 LLM 客户端。"""
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL_NAME
        self.name = "ScholarshipAgent"

    async def run(self, query: str, history_context: str = "", **kwargs) -> str:
        """处理奖助学金查询请求。

        Args:
            query: 用户原始问题
            history_context: 对话历史上下文（可选），用于理解上下文关联的提问
            **kwargs: 包含 scholarship_data 的关键字参数

        Returns:
            str: Agent 处理结果摘要

        Raises:
            LLMError: LLM 调用异常时抛出
        """
        scholarship_data = kwargs.get("scholarship_data")
        if scholarship_data is None:
            return "奖助学金数据获取失败，无法为您查询。请稍后再试或联系学生处。"

        scholarship_str = json.dumps(scholarship_data, ensure_ascii=False, indent=2)
        prompt = SCHOLARSHIP_PROMPT_TEMPLATE.format(
            scholarship_data=scholarship_str,
            user_question=query,
            history_context=history_context or "（无历史消息）",
        )

        role = kwargs.get("role", "student")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_system_prompt(role)},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            result = response.choices[0].message.content or ""
            logger.info(f"ScholarshipAgent 处理完成, 问题: {query[:50]}...")
            return result
        except Exception as e:
            logger.error(f"ScholarshipAgent LLM 调用异常: {e}", exc_info=True)
            raise LLMError(f"奖助学金查询处理失败: {str(e)}") from e
