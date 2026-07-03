"""手动执行 FAQ 向量入库脚本 — 加载文档、生成向量、存入数据库并 commit。"""

import asyncio
import sys
from pathlib import Path

# 确保从 ai-service 目录运行
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal
from app.rag.loader import process_and_store


async def main():
    print("=" * 60)
    print("  FAQ 向量手动入库")
    print("=" * 60)

    data_dir = str(Path(__file__).resolve().parent / "data" / "faq")
    print(f"  数据目录: {data_dir}")

    db = SessionLocal()
    try:
        count = await process_and_store(db, data_dir)
        db.commit()
        print(f"\n  [OK] 入库完成，共 {count} 条向量记录，已 commit 到数据库")
    except Exception as e:
        db.rollback()
        print(f"\n  [ERROR] 入库失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
