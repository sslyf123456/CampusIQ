"""异常处理与兜底逻辑模块。"""

import logging

logger = logging.getLogger(__name__)


class CampusServiceError(Exception):
    """campus-service 调用异常。

    当 campus-service 返回非200状态码或连接失败时抛出此异常。
    """

    def __init__(self, message: str = "campus-service 调用失败") -> None:
        """初始化 CampusServiceError。

        Args:
            message: 错误描述信息
        """
        self.message = message
        super().__init__(self.message)


class LLMError(Exception):
    """LLM 调用异常。

    当 OpenAI/兼容 API 调用失败时抛出此异常。
    """

    def __init__(self, message: str = "LLM 调用失败") -> None:
        """初始化 LLMError。

        Args:
            message: 错误描述信息
        """
        self.message = message
        super().__init__(self.message)


class EmbeddingError(Exception):
    """Embedding 调用异常。

    当 Embedding API 调用失败时抛出此异常。
    """

    def __init__(self, message: str = "Embedding 调用失败") -> None:
        """初始化 EmbeddingError。

        Args:
            message: 错误描述信息
        """
        self.message = message
        super().__init__(self.message)


# 全局兜底回复模板
FALLBACK_MESSAGES = {
    "campus_service_error": "校园数据服务暂时不可用，请稍后再试。",
    "llm_error": "AI 服务暂时不可用，请稍后再试。",
    "embedding_error": "知识库检索暂时不可用，请稍后再试。",
    "general_error": "服务异常，请稍后再试。如有校园相关问题，欢迎继续咨询。",
    "out_of_scope": "该问题超出校园服务范围，无法为您解答。如有校园相关问题，欢迎继续咨询。",
    "no_data": "暂无相关数据，请稍后再试或联系相关部门。",
    "clarify": "您的问题我暂时无法理解，能否再详细描述一下您想了解的内容？",
    "unclear_intent": "您的问题我暂时无法理解，能否再详细描述一下您想了解的内容？",
}


def get_fallback_message(error_type: str) -> str:
    """获取兜底回复消息。

    Args:
        error_type: 错误类型键名

    Returns:
        str: 兜底回复消息文本
    """
    return FALLBACK_MESSAGES.get(error_type, FALLBACK_MESSAGES["general_error"])
