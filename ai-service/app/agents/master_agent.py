"""主 Agent — 意图识别、路由分发、结果汇总。"""

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.chat import IntentResult
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)

# 意图类别定义
INTENT_CATEGORIES = {
    "schedule": "课表查询 — 用户询问课程安排、上课时间、教室等信息",
    "repair": "宿舍报修查询 — 用户询问报修进度、报修记录等信息",
    "scholarship": "奖助学金查询 — 用户询问奖学金、助学金申请、评定等信息",
    "notice": "通知检索 — 用户寻找校园通知、公告、通知公告等信息",
    "faq": "FAQ知识库 — 用户询问校园常见问题，如选课流程、宿舍管理、请假、图书馆等",
    "unclear": "意图模糊 — 用户的问题不够明确，需要反问澄清",
    "out_of_scope": "超出范围 — 用户的问题不属于校园服务范畴",
}

INTENT_PROMPT_TEMPLATE = """你是一个校园问答系统的意图识别引擎。请根据用户的消息判断其意图类别。

可选意图类别及描述：
{intent_descriptions}

请分析以下用户消息，返回JSON格式结果：
- intent: 识别到的意图类别（必须是上述类别之一）
- confidence: 置信度（0.0-1.0）
- clarify_question: 如果意图为unclear，请给出反问建议；否则为null
- keyword: 如果意图为notice，请提取用户想搜索的通知关键词；否则为null

用户消息：{user_message}

对话历史（最近消息）：
{history_context}

请仅返回JSON，不要添加其他文字。"""


class MasterAgent:
    """主 Agent，负责意图识别和路由分发。"""

    def __init__(self) -> None:
        """初始化 MasterAgent，创建 LLM 客户端。"""
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL_NAME

    async def identify_intent(self, user_message: str, history_context: str = "") -> IntentResult:
        """使用 LLM 分析用户消息，判断意图类别。

        Args:
            user_message: 用户输入的消息文本
            history_context: 对话历史上下文（可选），用于理解上下文关联的提问

        Returns:
            IntentResult: 意图识别结果

        Raises:
            LLMError: LLM 调用异常时抛出
        """
        intent_descriptions = "\n".join(
            f"- {key}: {desc}" for key, desc in INTENT_CATEGORIES.items()
        )
        prompt = INTENT_PROMPT_TEMPLATE.format(
            intent_descriptions=intent_descriptions,
            user_message=user_message,
            history_context=history_context or "（无历史消息）",
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content or ""
            logger.info(f"意图识别原始响应: {raw_content}")

            # 解析 LLM 返回的 JSON
            parsed = json.loads(raw_content)
            return IntentResult(
                intent=parsed.get("intent", "unclear"),
                confidence=float(parsed.get("confidence", 0.5)),
                clarify_question=parsed.get("clarify_question"),
                keyword=parsed.get("keyword"),
            )
        except json.JSONDecodeError as e:
            logger.error(f"意图识别 JSON 解析失败: {e}, raw: {raw_content}")
            return IntentResult(
                intent="unclear",
                confidence=0.0,
                clarify_question="您的问题我暂时无法理解，能否再详细描述一下您想了解的内容？",
            )
        except Exception as e:
            logger.error(f"意图识别 LLM 调用异常: {e}", exc_info=True)
            raise LLMError(f"意图识别失败: {str(e)}") from e

    async def run(self, query: str, history_context: str = "", **kwargs) -> IntentResult:
        """Agent 核心执行方法（供 ChatService 统一调用）。

        Args:
            query: 用户查询内容
            history_context: 对话历史上下文（可选），用于理解上下文关联的提问
            **kwargs: 扩展参数（当前未使用）

        Returns:
            IntentResult: 意图识别结果
        """
        return await self.identify_intent(query, history_context=history_context)
