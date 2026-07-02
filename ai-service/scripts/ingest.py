"""FAQ 向量化入库脚本 — 初始化运行一次，将 data/faq/ 文档向量化存入数据库。

使用方法：
    cd ai-service
    python scripts/ingest.py

前置条件：
    1. PostgreSQL + pgvector 扩展已安装
    2. campus_qa 数据库已创建并执行了 init.sql
    3. .env 文件已配置 EMBEDDING_API_KEY 和数据库连接信息
"""

import asyncio
import logging
import os
import sys

# 确保可以 import app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import SessionLocal
from app.rag.loader import FAQLoader
from app.rag.embedding import get_embedding
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


async def ingest_faq_documents(data_dir: str = None) -> None:
    """将 FAQ 文档向量化入库。

    Args:
        data_dir: FAQ 文档目录路径（默认使用 settings 或项目内 data/faq/）
    """
    if data_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", "faq")

    logger.info(f"开始 FAQ 文档入库，目录: {data_dir}")

    # 1. 加载 FAQ 文档并分块
    loader = FAQLoader()
    documents = loader.load_all(data_dir)

    if not documents:
        logger.warning("未找到任何 FAQ 文档，请检查 data/faq/ 目录")
        return

    logger.info(f"加载了 {len(documents)} 个文档块")

    # 2. 逐块向量化并存入数据库
    vector_store = VectorStore()
    db = SessionLocal()

    success_count = 0
    fail_count = 0

    try:
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            document_name = doc.get("document", "unknown")
            chunk_index = doc.get("chunk_index", i)

            if not content.strip():
                continue

            try:
                embedding = await get_embedding(content)
                vector_store.store_embedding(
                    db=db,
                    document=document_name,
                    chunk_index=chunk_index,
                    content=content,
                    embedding=embedding,
                )
                success_count += 1
                logger.info(f"入库成功 [{i+1}/{len(documents)}]: {document_name} chunk_{chunk_index}")
            except Exception as e:
                fail_count += 1
                logger.error(f"入库失败 [{i+1}/{len(documents)}]: {document_name} chunk_{chunk_index}: {e}")

        db.commit()
        logger.info(f"FAQ 入库完成！成功: {success_count}, 失败: {fail_count}")

    except Exception as e:
        db.rollback()
        logger.error(f"FAQ 入库异常，已回滚: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(ingest_faq_documents())
