"""文档向量化（Embedding 调用）— 使用 OpenAI 兼容接口将文本转换为向量。"""

import logging
from typing import List

from openai import AsyncOpenAI

from app.config import settings
from app.utils.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

# 创建 Embedding 客户端（独立配置，支持与 LLM 不同的 API Key/Base URL）
_embedding_client = AsyncOpenAI(
    api_key=settings.EMBEDDING_API_KEY,
    base_url=settings.EMBEDDING_BASE_URL,
)
_embedding_model = settings.EMBEDDING_MODEL_NAME
_embedding_dimensions = settings.EMBEDDING_DIMENSIONS


async def get_embedding(text: str) -> List[float]:
    """将单条文本转换为向量。

    Args:
        text: 需要向量化的文本内容

    Returns:
        List[float]: 向量列表（维度由 EMBEDDING_DIMENSIONS 配置决定）

    Raises:
        EmbeddingError: Embedding API 调用异常时抛出
    """
    try:
        response = await _embedding_client.embeddings.create(
            model=_embedding_model,
            input=text,
            dimensions=_embedding_dimensions,
        )
        embedding = response.data[0].embedding
        logger.info(f"文本向量化完成, 输入长度: {len(text)}, 向量维度: {len(embedding)}")
        return embedding
    except Exception as e:
        logger.error(f"Embedding 调用异常: {e}", exc_info=True)
        raise EmbeddingError(f"文本向量化失败: {str(e)}") from e


async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """将多条文本批量转换为向量。

    Args:
        texts: 需要向量化的文本列表

    Returns:
        List[List[float]]: 向量列表，每个元素对应一条文本的向量

    Raises:
        EmbeddingError: Embedding API 调用异常时抛出
    """
    try:
        response = await _embedding_client.embeddings.create(
            model=_embedding_model,
            input=texts,
            dimensions=_embedding_dimensions,
        )
        embeddings = [item.embedding for item in response.data]
        logger.info(f"批量向量化完成, 输入数量: {len(texts)}")
        return embeddings
    except Exception as e:
        logger.error(f"批量 Embedding 调用异常: {e}", exc_info=True)
        raise EmbeddingError(f"批量文本向量化失败: {str(e)}") from e
