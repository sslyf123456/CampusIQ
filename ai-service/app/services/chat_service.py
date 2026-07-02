"""对话编排核心服务 — 意图识别 → 路由 → Sub-Agent 执行 → SSE 推送。

SSE 事件类型统一为架构师设计：
- thinking: 思考中/处理进行中提示
- agent_call: Sub-Agent 开始处理
- result: 最终回答（流式逐字输出）
- error: 错误信息
- done: 流结束标记
- clarify: 反问澄清
"""

import json
import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from app.config import settings
from app.schemas.chat import SSEEvent
from app.agents.master_agent import MasterAgent
from app.agents.schedule_agent import ScheduleAgent
from app.agents.repair_agent import RepairAgent
from app.agents.scholarship_agent import ScholarshipAgent
from app.agents.notice_agent import NoticeAgent
from app.agents.faq_agent import FAQAgent
from app.services.campus_client import CampusClient
from app.services.conversation_service import ConversationService
from app.utils.exceptions import LLMError, CampusServiceError
from app.utils.exceptions import FALLBACK_MESSAGES

logger = logging.getLogger(__name__)

# 最终回答的 LLM Prompt 模板
ANSWER_PROMPT_TEMPLATE = """你是一个校园智能问答助手。请根据以下信息，生成对用户问题的自然语言回答。

用户问题：{user_question}

Agent 处理结果：
{agent_result}

要求：
1. 用自然、友好的语言回答，不要生硬地罗列数据
2. 如果数据为空或 Agent 返回兜底提示，请如实告知用户
3. 回答要简洁清晰，不要过长"""


class ChatService:
    """对话编排服务，协调 Master Agent、Sub-Agent 和 SSE 推送。"""

    def __init__(self) -> None:
        """初始化 ChatService，创建所有 Agent 和服务实例。"""
        self.master_agent = MasterAgent()
        # 使用字典管理 Sub-Agent，方便按意图名称路由
        self.sub_agents = {
            "schedule": ScheduleAgent(),
            "repair": RepairAgent(),
            "scholarship": ScholarshipAgent(),
            "notice": NoticeAgent(),
            "faq": FAQAgent(),
        }
        self.campus_client = CampusClient()
        self.conversation_service = ConversationService()
        self.llm_client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.llm_model = settings.LLM_MODEL_NAME

    async def stream_chat(
        self,
        db: Session,
        token: str,
        student_db_id: int,
        conversation_id: Optional[int],
        user_message: str,
    ) -> AsyncGenerator[SSEEvent, None]:
        """对话编排主流程 — 意图识别 → 路由 → Sub-Agent → SSE 流式输出。

        Args:
            db: 数据库会话
            token: 用户 JWT token（透传给 campus-service）
            student_db_id: 学生数据库主键ID（从 JWT 的 db_id 字段获取）
            conversation_id: 会话ID（为空则自动创建）
            user_message: 用户消息内容

        Yields:
            SSEEvent: SSE 事件（thinking/agent_call/result/error/done/clarify）
        """
        try:
            # 1. 确保会话存在
            if not conversation_id:
                conv = self.conversation_service.create_conversation(db, student_db_id)
                conversation_id = conv.id

            # 2. 保存用户消息
            self.conversation_service.add_message(
                db, conversation_id, "user", user_message
            )

            # 3. 获取历史消息作为上下文（最近 10 条）
            history_messages = self.conversation_service.get_messages(db, conversation_id, limit=10)
            history_context = "\n".join(
                f"{m.role}: {m.content}" for m in history_messages
            )

            # 4. 推送 thinking 事件 — 正在分析意图
            yield SSEEvent(event="thinking", data=json.dumps({
                "content": "正在分析您的问题...",
                "clarify": False,
            }))

            # 5. Master Agent 意图识别
            intent_result = await self.master_agent.run(user_message)

            # 6. 根据意图结果路由
            if intent_result.intent == "unclear":
                # 模糊意图 → 反问澄清
                clarify_question = intent_result.clarify_question or FALLBACK_MESSAGES["unclear_intent"]
                yield SSEEvent(event="clarify", data=json.dumps({"question": clarify_question}))
                self.conversation_service.add_message(
                    db, conversation_id, "assistant", clarify_question,
                    agent_name="MasterAgent",
                    metadata={"event": "clarify"},
                )
                yield SSEEvent(event="done", data=json.dumps({}))
                return

            if intent_result.intent == "out_of_scope":
                # 超出范围 → 兜底回复
                fallback = FALLBACK_MESSAGES["out_of_scope"]
                yield SSEEvent(event="error", data=json.dumps({
                    "message": fallback,
                    "fallback": True,
                }))
                self.conversation_service.add_message(
                    db, conversation_id, "assistant", fallback,
                    agent_name="MasterAgent",
                )
                yield SSEEvent(event="done", data=json.dumps({}))
                return

            # 7. 路由到对应 Sub-Agent
            agent_name = intent_result.intent
            yield SSEEvent(event="agent_call", data=json.dumps({
                "agent": agent_name,
                "description": f"正在调用 {agent_name} Agent 处理您的问题...",
            }))

            agent_result = None

            if intent_result.intent == "schedule":
                schedule_data = await self.campus_client.get_schedule(token)
                agent_result = await self.sub_agents["schedule"].run(
                    user_message, schedule_data=schedule_data
                )

            elif intent_result.intent == "repair":
                repair_data = await self.campus_client.get_repair(token)
                agent_result = await self.sub_agents["repair"].run(
                    user_message, repair_data=repair_data
                )

            elif intent_result.intent == "scholarship":
                scholarship_data = await self.campus_client.get_scholarship(token)
                agent_result = await self.sub_agents["scholarship"].run(
                    user_message, scholarship_data=scholarship_data
                )

            elif intent_result.intent == "notice":
                keyword = intent_result.keyword or user_message
                notice_data = await self.campus_client.get_notices(token, keyword)
                agent_result = await self.sub_agents["notice"].run(
                    user_message, notice_data=notice_data
                )

            elif intent_result.intent == "faq":
                agent_result = await self.sub_agents["faq"].run(
                    user_message, db=db
                )

            else:
                # 未知意图 → FAQ 兜底
                agent_result = await self.sub_agents["faq"].run(
                    user_message, db=db
                )

            # 8. 使用 LLM 流式生成最终自然语言回答（SSE result 事件，逐 token 推送）
            answer_prompt = ANSWER_PROMPT_TEMPLATE.format(
                user_question=user_message,
                agent_result=agent_result,
            )

            messages = []
            if history_context:
                messages.append({"role": "system", "content": f"对话历史:\n{history_context}"})
            messages.append({"role": "user", "content": answer_prompt})

            full_answer = ""
            try:
                stream = await self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=messages,
                    temperature=0.5,
                    max_tokens=1000,
                    stream=True,
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        full_answer += text
                        yield SSEEvent(event="result", data=json.dumps({
                            "content": text,
                            "agent": agent_name,
                        }))
            except Exception as e:
                logger.error(f"LLM 流式生成异常: {e}", exc_info=True)
                if agent_result:
                    full_answer = agent_result
                    yield SSEEvent(event="result", data=json.dumps({
                        "content": agent_result,
                        "agent": agent_name,
                    }))
                else:
                    yield SSEEvent(event="error", data=json.dumps({
                        "message": FALLBACK_MESSAGES["llm_error"],
                    }))

            # 9. 保存 AI 回复到数据库
            self.conversation_service.add_message(
                db, conversation_id, "assistant", full_answer,
                agent_name=agent_name,
            )

            # 10. 推送 done 事件 — 流结束
            yield SSEEvent(event="done", data=json.dumps({}))

        except LLMError as e:
            logger.error(f"ChatService LLM 错误: {e}", exc_info=True)
            yield SSEEvent(event="error", data=json.dumps({"message": FALLBACK_MESSAGES["llm_error"]}))
            yield SSEEvent(event="done", data=json.dumps({}))

        except CampusServiceError as e:
            logger.error(f"ChatService 校园服务错误: {e}", exc_info=True)
            yield SSEEvent(event="error", data=json.dumps({"message": FALLBACK_MESSAGES["campus_service_error"]}))
            yield SSEEvent(event="done", data=json.dumps({}))

        except Exception as e:
            logger.error(f"ChatService 未预期异常: {e}", exc_info=True)
            yield SSEEvent(event="error", data=json.dumps({"message": FALLBACK_MESSAGES["general_error"]}))
            yield SSEEvent(event="done", data=json.dumps({}))
