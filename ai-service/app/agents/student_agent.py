"""学生信息查询 Agent — 接收学生数据，结合用户问题生成回答。"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.prompts import get_system_prompt
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)

STUDENT_PROMPT_TEMPLATE = """你是一个校园学生信息查询助手。根据以下学生数据，回答用户的问题。

学生数据（JSON）：
{student_data}

字段说明：
- student_id: 学号
- name: 姓名
- gender: 性别（male=男, female=女）
- department: 院系
- major: 专业
- phone: 联系电话
- email: 邮箱
- birth_date: 出生日期
- enrollment_year: 入学年份
- dorm_building: 宿舍楼
- dorm_room: 宿舍号

用户问题：{user_question}

对话历史（最近消息）：
{history_context}

请严格根据学生数据回答，不要编造数据中不存在的信息。如果数据为空，请告知用户暂无学生信息。
回答时请整理学生信息，包括学号、姓名、性别、院系、专业、宿舍等关键字段。
注意：回答中不要使用任何emoji表情符号，用纯文字即可。"""


class StudentAgent:
    """学生信息查询 Agent，处理与学生信息相关的用户问题。"""

    def __init__(self) -> None:
        """初始化 StudentAgent，创建 LLM 客户端。"""
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL_NAME
        self.name = "StudentAgent"

    async def run(self, query: str, history_context: str = "", **kwargs) -> str:
        """处理学生信息查询请求。

        Args:
            query: 用户原始问题
            history_context: 对话历史上下文（可选），用于理解上下文关联的提问
            **kwargs: 包含 student_data 的关键字参数

        Returns:
            str: Agent 处理结果摘要

        Raises:
            LLMError: LLM 调用异常时抛出
        """
        student_data = kwargs.get("student_data")
        if student_data is None:
            return "学生信息查询功能仅对管理员开放，或数据获取失败，无法为您查询。"

        data = student_data.get("data", student_data)
        if not data:
            return "暂无学生信息。"

        student_str = json.dumps(data, ensure_ascii=False, indent=2)
        prompt = STUDENT_PROMPT_TEMPLATE.format(
            student_data=student_str,
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
            logger.info(f"StudentAgent 处理完成, 问题: {query[:50]}...")
            return result
        except Exception as e:
            logger.error(f"StudentAgent LLM 调用异常: {e}", exc_info=True)
            raise LLMError(f"学生信息查询处理失败: {str(e)}") from e
