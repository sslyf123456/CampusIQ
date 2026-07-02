"""数据库连接模块 — SQLAlchemy 连接 PostgreSQL（campus_qa 数据库），使用 ai_campus schema。"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""
    pass


# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """获取数据库会话的依赖注入函数。

    Yields:
        Session: SQLAlchemy 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
