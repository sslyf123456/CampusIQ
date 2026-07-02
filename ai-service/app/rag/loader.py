"""FAQ 文档加载与分块 — 从 data/faq/ 目录加载文档，分块后向量化入库。"""

import os
import logging
from typing import List, Dict

from sqlalchemy.orm import Session

from app.config import settings
from app.rag.embedding import get_embedding, get_embeddings_batch
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

# 分块参数
CHUNK_SIZE = 500  # 每个分块的最大字符数
CHUNK_OVERLAP = 100  # 分块之间的重叠字符数


class FAQLoader:
    """FAQ 文档加载器，负责扫描目录、加载 Markdown、按标题分块。

    架构师设计要求按 Markdown ## 标题切分，保留上下文重叠。
    """

    def __init__(self, data_dir: str = None) -> None:
        """初始化 FAQLoader。

        Args:
            data_dir: FAQ 文档目录路径（默认使用项目内 data/faq/）
        """
        self.data_dir = data_dir

    def load_all(self, data_dir: str = None) -> List[Dict[str, str]]:
        """加载目录下所有 .md FAQ 文档并按标题分块。

        Args:
            data_dir: FAQ 文档目录路径（覆盖默认值）

        Returns:
            List[Dict]: 分块文档列表，每个包含 document、chunk_index、content
        """
        dir_path = data_dir or self.data_dir
        if not dir_path:
            logger.warning("未指定 FAQ 数据目录")
            return []

        raw_documents = load_faq_documents(dir_path)
        chunked_documents: List[Dict[str, str]] = []

        for doc in raw_documents:
            chunks = split_by_heading(doc["content"], doc["document"])
            chunked_documents.extend(chunks)

        logger.info(f"加载并分块了 {len(chunked_documents)} 个文档片段")
        return chunked_documents

    def split_by_heading(self, text: str, source: str) -> List[Dict[str, str]]:
        """按 Markdown ## 标题切分文本。

        Args:
            text: 原始文本
            source: 来源文件名

        Returns:
            List[Dict]: 分块结果，每个包含 document、chunk_index、content
        """
        return split_by_heading(text, source)


def split_by_heading(text: str, source: str) -> List[Dict[str, str]]:
    """按 Markdown ## 标题切分文本，保留标题作为上下文。

    Args:
        text: 原始文本内容
        source: 来源文件名

    Returns:
        List[Dict]: 分块结果列表
    """
    import re

    # 按 ## 标题分割
    sections = re.split(r'\n## ', text)

    chunks: List[Dict[str, str]] = []
    chunk_index = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # 如果是第一个 section，可能包含 # 标题（文档标题）
        # 补上 ## 前缀（除了第一段）
        if chunk_index > 0 and not section.startswith('#'):
            section = '## ' + section

        # 如果 section 过长，进一步分块
        if len(section) > CHUNK_SIZE:
            sub_chunks = chunk_text(section)
            for sub in sub_chunks:
                chunks.append({
                    "document": source,
                    "chunk_index": chunk_index,
                    "content": sub,
                })
                chunk_index += 1
        else:
            chunks.append({
                "document": source,
                "chunk_index": chunk_index,
                "content": section,
            })
            chunk_index += 1

    return chunks


def load_faq_documents(data_dir: str) -> List[Dict[str, str]]:
    """从 data/faq/ 目录加载所有 .md 文件。

    Args:
        data_dir: FAQ 文档目录路径

    Returns:
        List[Dict]: 文档列表，每个包含 document(文件名) 和 content(文本内容)
    """
    documents: List[Dict[str, str]] = []
    if not os.path.exists(data_dir):
        logger.warning(f"FAQ 数据目录不存在: {data_dir}")
        return documents

    for filename in os.listdir(data_dir):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            documents.append({
                "document": filename,
                "content": content,
            })
            logger.info(f"加载 FAQ 文档: {filename}, 内容长度: {len(content)}")
        except Exception as e:
            logger.error(f"加载 FAQ 文档失败: {filename}, 错误: {e}")

    return documents


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """将文本分块，支持重叠以保留上下文连贯性。

    Args:
        text: 需要分块的原始文本
        chunk_size: 每个分块的最大字符数
        overlap: 分块之间的重叠字符数

    Returns:
        List[str]: 分块后的文本列表
    """
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # 如果不是最后一块，尝试在重叠区域找到自然的断句点
        if end < len(text):
            search_start = max(end - overlap, start)
            natural_break_pos = -1
            for i in range(end - 1, search_start, -1):
                if text[i] in ("\n", ".", "。", "！", "！"):
                    natural_break_pos = i + 1
                    break
            if natural_break_pos > 0:
                end = natural_break_pos
                chunk = text[start:end]

        chunks.append(chunk.strip())
        start = end - overlap

        if start >= len(text):
            break

    # 去除空块
    chunks = [c for c in chunks if c]
    return chunks


async def process_and_store(db: Session, data_dir: str) -> int:
    """加载文档 → 分块 → 向量化 → 存入数据库的完整流程。

    Args:
        db: 数据库会话
        data_dir: FAQ 文档目录路径

    Returns:
        int: 入库的向量记录总数
    """
    documents = load_faq_documents(data_dir)
    if not documents:
        logger.warning("未找到任何 FAQ 文档，跳过向量入库")
        return 0

    vector_store = VectorStore()

    total_entries = 0

    for doc in documents:
        chunks = chunk_text(doc["content"])
        logger.info(f"文档 {doc['document']} 分块数: {len(chunks)}")

        # 批量向量化
        try:
            embeddings = await get_embeddings_batch(chunks)
        except Exception as e:
            logger.error(f"文档 {doc['document']} 向量化失败: {e}", exc_info=True)
            continue

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            try:
                vector_store.store_embedding(
                    db=db,
                    document=doc["document"],
                    chunk_index=i,
                    content=chunk,
                    embedding=embedding,
                )
                total_entries += 1
            except Exception as e:
                logger.error(f"文档 {doc['document']} 第 {i} 块存储失败: {e}")
                continue

    logger.info(f"FAQ 向量入库完成, 总记录数: {total_entries}")
    return total_entries
