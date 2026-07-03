"""FAQ 知识库兜底 Agent — 使用 RAG 向量检索回答问题。"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.prompts import get_system_prompt
from app.rag.vector_store import VectorStore
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)

FAQ_PROMPT_TEMPLATE = """你是一个校园FAQ知识库助手。根据以下检索到的知识库文档片段，回答用户的问题。

知识库检索结果：
{faq_context}

用户问题：{user_question}

对话历史（最近消息）：
{history_context}

请根据知识库内容给出清晰、准确的回答。如果知识库内容无法匹配用户问题，请告知用户该问题超出服务范围，无法为您解答。
回答时请引用相关的具体规定或流程。
注意：回答中不要使用任何emoji表情符号，用纯文字即可。"""


class FAQAgent:
    """FAQ 知识库兜底 Agent，使用向量检索获取相关文档后生成回答。"""

    def __init__(self) -> None:
        """初始化 FAQAgent，创建 LLM 客户端和向量存储。"""
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL_NAME
        self.name = "FAQAgent"
        self.vector_store = VectorStore()

    async def run(self, query: str, history_context: str = "", **kwargs) -> str:
        """处理 FAQ 知识库查询请求。

        Args:
            query: 用户原始问题
            history_context: 对话历史上下文（可选），用于理解上下文关联的提问
            **kwargs: 包含 db 的关键字参数（用于向量检索）

        Returns:
            str: Agent 处理结果摘要

        Raises:
            LLMError: LLM 调用异常时抛出
        """
        db = kwargs.get("db")
        # 通过向量检索获取相关文档片段
        from app.rag.embedding import get_embedding

        try:
            query_embedding = await get_embedding(query)
            similar_docs = self.vector_store.search_similar(db, query_embedding, top_k=5)

            if not similar_docs:
                return "该问题超出服务范围，无法为您解答。如有其他校园相关问题，欢迎继续咨询。"

            # 组合检索结果作为上下文
            faq_context_parts = []
            for doc in similar_docs:
                content = doc.get("content", "")
                source = doc.get("document", "未知来源")
                faq_context_parts.append(f"[来源: {source}]\n{content}")
            faq_context = "\n\n---\n\n".join(faq_context_parts)

            prompt = FAQ_PROMPT_TEMPLATE.format(
                faq_context=faq_context,
                user_question=query,
                history_context=history_context or "（无历史消息）",
            )

            role = kwargs.get("role", "student")
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
            logger.info(f"FAQAgent 处理完成, 问题: {query[:50]}...")
            return result
        except Exception as e:
            logger.error(f"FAQAgent 处理异常: {e}", exc_info=True)
            return "该问题超出服务范围，无法为您解答。如有其他校园相关问题，欢迎继续咨询。"
