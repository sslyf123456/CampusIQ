"""Agent 抽象基类 — 统一所有 Agent 的接口规范。"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """所有 Agent 的抽象基类，统一接口和 LLM 客户端管理。

    每个 Sub-Agent 必须实现：
    - name: Agent 名称标识
    - description: Agent 功能描述
    - run(): 核心执行方法
    - build_prompt(): Prompt 构建方法
    """

    name: str = "base"
    description: str = "基础 Agent"

    def __init__(self) -> None:
        """初始化 BaseAgent，创建共享 LLM 客户端。"""
        self.llm_client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.llm_model = settings.LLM_MODEL_NAME

    @abstractmethod
    async def run(self, query: str, **kwargs: Any) -> str:
        """Agent 核心执行方法。

        Args:
            query: 用户查询内容
            **kwargs: Agent 特定参数（如 campus 数据、JWT token 等）

        Returns:
            str: Agent 处理结果（供 ChatService 汇总后推送 SSE）

        Raises:
            LLMError: LLM 调用异常
        """
        ...

    @abstractmethod
    def build_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """构建 Agent 特定的 Prompt。

        Args:
            query: 用户查询内容
            context: 上下文数据（如 campus 返回数据、FAQ 检索结果等）

        Returns:
            str: 构建好的完整 Prompt
        """
        ...

    async def _call_llm(self, prompt: str, temperature: float = 0.3, max_tokens: int = 800) -> str:
        """调用 LLM 生成回答（非流式，Sub-Agent 内部使用）。

        Args:
            prompt: 完整 Prompt
            temperature: 生成温度
            max_tokens: 最大 token 数

        Returns:
            str: LLM 生成的文本结果
        """
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result = response.choices[0].message.content or ""
            logger.info(f"{self.name} LLM 调用完成, 输入长度: {len(prompt)}")
            return result
        except Exception as e:
            logger.error(f"{self.name} LLM 调用异常: {e}", exc_info=True)
            raise
