"""向量存储与检索（pgvector 操作）— 存储和检索 FAQ 文档向量。"""

import logging
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储服务，使用 pgvector 存储和检索 FAQ 文档向量。"""

    def store_embedding(
        self,
        db: Session,
        document: str,
        chunk_index: int,
        content: str,
        embedding: List[float],
    ) -> None:
        """将文档分块向量存入数据库。

        Args:
            db: 数据库会话
            document: 来源文档名
            chunk_index: 分块序号
            content: 原始文本片段
            embedding: 向量数据
        """
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
        sql = text("""
            INSERT INTO ai_campus.faq_embeddings (document, chunk_index, content, embedding)
            VALUES (:document, :chunk_index, :content, CAST(:embedding AS vector))
        """)
        db.execute(sql, {
            "document": document,
            "chunk_index": chunk_index,
            "content": content,
            "embedding": embedding_str,
        })
        # 不在此处 commit，由调用方统一管理事务提交
        logger.info(f"向量入库: document={document}, chunk_index={chunk_index}")

    def search_similar(
        self,
        db: Session,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """通过余弦相似度检索最相似的文档片段。

        Args:
            db: 数据库会话
            query_embedding: 查询向量
            top_k: 返回最相似的 K 个文档片段

        Returns:
            List[Dict]: 相似文档片段列表，每个包含 document, chunk_index, content, similarity
        """
        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
        sql = text("""
            SELECT document, chunk_index, content,
                   1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM ai_campus.faq_embeddings
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)
        result = db.execute(sql, {
            "query_embedding": embedding_str,
            "top_k": top_k,
        })
        rows = result.fetchall()
        similar_docs = [
            {
                "document": row[0],
                "chunk_index": row[1],
                "content": row[2],
                "similarity": float(row[3]),
            }
            for row in rows
        ]
        logger.info(f"向量检索完成, 返回 {len(similar_docs)} 条相似文档")
        return similar_docs

    def check_embeddings_exist(self, db: Session) -> bool:
        """检查 FAQ 向量是否已入库。

        Args:
            db: 数据库会话

        Returns:
            bool: 是否已有向量数据
        """
        sql = text("SELECT COUNT(*) FROM ai_campus.faq_embeddings")
        result = db.execute(sql)
        count = result.scalar()
        return count > 0
