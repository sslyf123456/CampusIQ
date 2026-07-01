#!/usr/bin/env python3
"""
PG + pgvector 冒烟测试脚本

验证项：
  1. PostgreSQL 连接是否正常
  2. pgvector 扩展是否可用
  3. 向量类型基本操作（插入、查询、距离计算）
  4. init.sql 建表脚本能否正常执行

用法：
  python data/smoke_test_pg.py

依赖：
  pip install psycopg2-binary python-dotenv
"""

import os
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql, errors
except ImportError:
    print("[FAIL] 缺少依赖：psycopg2，请执行 pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("[FAIL] 缺少依赖：python-dotenv，请执行 pip install python-dotenv")
    sys.exit(1)


# 加载 .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    print(f"[WARN] 未找到 .env 文件：{ENV_PATH}，将使用环境变量或默认值")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "campus_qa")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

results = []


def check(label, ok, detail=""):
    tag = PASS if ok else FAIL
    line = f"  {tag} {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    results.append(ok)


def get_conn():
    '''
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        options="-c lc_messages=C",
    )
    '''
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="campus_qa",
        user="postgres",
        password="123456",
        options="-c lc_messages=C",
        client_encoding='UTF8'
    )
    conn.set_client_encoding("UTF8")
    return conn


def test_connection():
    """测试 1：基本连接"""
    print("\n=== 1. PostgreSQL 连接测试 ===")
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        check("数据库连接", True, version[:60])
        cur.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        check("数据库连接", False, f"OperationalError: {e}")
        return False
    except Exception as e:
        check("数据库连接", False, f"{type(e).__name__}: {e}")
        return False


def test_pgvector_extension():
    """测试 2：pgvector 扩展"""
    print("\n=== 2. pgvector 扩展测试 ===")
    try:
        conn = get_conn()
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        check("CREATE EXTENSION vector", True)

        cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        row = cur.fetchone()
        if row:
            check("vector 扩展已安装", True, f"v{row[0]}")
        else:
            check("vector 扩展已安装", False, "扩展未注册")
            cur.close()
            conn.close()
            return False

        cur.close()
        conn.close()
        return True
    except Exception as e:
        check("pgvector 扩展", False, str(e))
        return False


def test_vector_ops():
    """测试 3：向量基本操作"""
    print("\n=== 3. 向量操作测试 ===")
    try:
        conn = get_conn()
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("DROP TABLE IF EXISTS _smoke_vector_test;")
        cur.execute("CREATE TABLE _smoke_vector_test (id serial PRIMARY KEY, vec vector(3));")
        check("创建含 vector(3) 列的临时表", True)

        cur.execute("INSERT INTO _smoke_vector_test (vec) VALUES ('[1,0,0]'), ('[0,1,0]'), ('[0,0,1]');")
        check("插入 3 条向量", True)

        cur.execute("SELECT vec FROM _smoke_vector_test ORDER BY id;")
        rows = cur.fetchall()
        check(f"读回向量数据（{len(rows)} 条）", len(rows) == 3)

        cur.execute("""
            SELECT id, vec <=> '[1,0,0]' AS dist
            FROM _smoke_vector_test
            ORDER BY vec <=> '[1,0,0]'
            LIMIT 1;
        """)
        nearest = cur.fetchone()
        ok = nearest is not None and nearest[0] == 1
        check("余弦距离排序（<=> 操作符）", ok, f"最近 id={nearest[0]}, dist={nearest[1]}" if nearest else "无结果")

        cur.execute("DROP TABLE _smoke_vector_test;")
        check("清理临时表", True)

        cur.close()
        conn.close()
        return True
    except Exception as e:
        check("向量操作", False, str(e))
        return False


def test_init_sql():
    """测试 4：执行 init.sql 建表"""
    print("\n=== 4. init.sql 建表测试 ===")
    sql_path = PROJECT_ROOT / "data" / "init.sql"
    if not sql_path.exists():
        check(f"找到 {sql_path.name}", False, "文件不存在")
        return False
    check(f"找到 {sql_path.name}", True)

    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
    except Exception as e:
        check("读取 init.sql", False, str(e))
        return False
    check("读取 init.sql", True)

    try:
        conn = get_conn()
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(sql_content)
        check("执行 init.sql 建表", True)

        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('campus', 'ai_campus')
            ORDER BY table_schema, table_name;
        """)
        tables = cur.fetchall()
        expected = {
            ("campus", "students"),
            ("campus", "admins"),
            ("campus", "schedules"),
            ("campus", "student_schedule"),
            ("campus", "repair_orders"),
            ("campus", "scholarship_records"),
            ("campus", "notices"),
            ("ai_campus", "faq_embeddings"),
            ("ai_campus", "conversations"),
            ("ai_campus", "messages"),
        }
        actual = set(tables)
        missing = expected - actual
        extra = actual - expected

        check(f"表数量（期望 {len(expected)}，实际 {len(actual)}）", len(actual) == len(expected))

        if missing:
            check("缺失的表", False, ", ".join(f"{s}.{t}" for s, t in sorted(missing)))
        else:
            check("所有期望表已创建", True)

        if extra:
            print(f"  {INFO} 额外表（不影响）：{', '.join(f'{s}.{t}' for s, t in sorted(extra))}")

        cur.close()
        conn.close()
        return len(missing) == 0
    except Exception as e:
        check("执行 init.sql", False, str(e))
        return False


def test_ivfflat_index():
    """测试 5：IVFFlat 索引是否正常创建"""
    print("\n=== 5. IVFFlat 索引测试 ===")
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'ai_campus'
              AND tablename = 'faq_embeddings'
              AND indexname = 'idx_faq_embedding';
        """)
        row = cur.fetchone()
        if row:
            check("IVFFlat 索引存在", True, row[0])
        else:
            check("IVFFlat 索引存在", False, "未找到 idx_faq_embedding")

        cur.close()
        conn.close()
        return row is not None
    except Exception as e:
        check("IVFFlat 索引", False, str(e))
        return False


def cleanup():
    """清理：删除 schema，让下次运行 init.sql 不冲突"""
    print("\n=== 清理 ===")
    try:
        conn = get_conn()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP SCHEMA IF EXISTS campus CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS ai_campus CASCADE;")
        cur.execute("DROP EXTENSION IF EXISTS vector;")
        cur.close()
        conn.close()
        print(f"  {INFO} 已删除 campus、ai_campus schema 及 vector 扩展（保持干净环境）")
    except Exception as e:
        print(f"  {INFO} 清理跳过：{e}")


def main():
    print("=" * 60)
    print("  PG + pgvector 冒烟测试")
    print(f"  目标：{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("=" * 60)

    ok1 = test_connection()
    if not ok1:
        print("\n连接失败，后续测试跳过。请检查 .env 中的数据库配置。")
        _summary()
        sys.exit(1)

    ok2 = test_pgvector_extension()
    ok3 = test_vector_ops()
    ok4 = test_init_sql()
    ok5 = test_ivfflat_index() if ok4 else False

    cleanup()
    _summary()

    if all(results):
        print(f"\n{PASS} 全部通过！PG + pgvector 环境就绪。")
        sys.exit(0)
    else:
        print(f"\n{FAIL} 存在失败项，请根据上方输出排查。")
        sys.exit(1)


def _summary():
    total = len(results)
    passed = sum(results)
    failed = total - passed
    print("\n" + "=" * 60)
    print(f"  结果汇总：{passed} 通过 / {failed} 失败 / {total} 总计")
    print("=" * 60)


if __name__ == "__main__":
    main()
