"""配置管理模块 — 通过 .env 环境变量管理所有配置项。"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 明确指定 .env 文件路径（确保无论从哪个目录启动都能正确加载）
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Settings:
    """ai-service 全局配置，从环境变量读取。"""

    # PostgreSQL 连接（与 campus-service 共用同一数据库）
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "campus_qa")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "your_password_here")

    @property
    def DATABASE_URL(self) -> str:
        """构建 SQLAlchemy 数据库连接 URL。"""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # campus-service 地址
    CAMPUS_SERVICE_URL: str = os.getenv("CAMPUS_SERVICE_URL", "http://localhost:8000")

    # LLM 配置（支持 OpenAI 兼容接口，如 DeepSeek）
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "deepseek-chat")

    # Embedding 配置
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

    # JWT 配置（与 campus-service 共用同一密钥）
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your_jwt_secret_here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # AI 服务端口
    AI_SERVICE_PORT: int = int(os.getenv("AI_SERVICE_PORT", "8002"))

    # FAQ 数据目录
    FAQ_DATA_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "faq"
    )


settings = Settings()
