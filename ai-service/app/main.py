"""FastAPI 应用入口 — SSE 端点注册、中间件配置、启动初始化。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal
from app.routers import chat, conversations
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化 FAQ 向量，关闭时清理资源。"""
    logger.info("AI Service 启动，检查 FAQ 向量数据...")

    db = SessionLocal()
    try:
        vector_store = VectorStore()
        if not vector_store.check_embeddings_exist(db):
            logger.info("FAQ 向量数据不存在，尝试自动入库...")
            if settings.EMBEDDING_API_KEY and settings.FAQ_DATA_DIR:
                from app.rag.loader import process_and_store
                try:
                    count = await process_and_store(db, settings.FAQ_DATA_DIR)
                    logger.info(f"FAQ 自动入库完成, 共 {count} 条向量记录")
                except Exception as e:
                    logger.warning(f"FAQ 自动入库失败（可手动执行）: {e}")
            else:
                logger.warning("Embedding API Key 未配置或 FAQ 目录不存在，跳过自动入库")
        else:
            logger.info("FAQ 向量数据已存在，无需重新入库")
    finally:
        db.close()

    logger.info("AI Service 启动完成")

    yield  # 应用运行期间

    logger.info("AI Service 关闭中")


app = FastAPI(
    title="Campus QA - AI Service",
    version="1.0.0",
    description="基于 RAG + 多智能体校园问答助手 - AI 问答核心服务",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(conversations.router)


@app.get("/health")
def health():
    """健康检查端点。

    Returns:
        dict: 服务健康状态信息
    """
    return {
        "status": "ok",
        "service": "ai-service",
        "version": "1.0.0",
        "port": settings.AI_SERVICE_PORT,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.AI_SERVICE_PORT,
        reload=True,
    )
