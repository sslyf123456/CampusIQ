"""
演示数据导入脚本
从 campus-service/data/*.json 读取数据，导入 PostgreSQL。
依赖顺序：admins → students → schedules → student_schedule → repair_orders → scholarships → notices
密码通过 bcrypt 哈希后存储。
重复运行幂等：先清空所有 campus schema 表再导入（不影响 ai_campus）。
"""
import json
import os
import sys
from pathlib import Path

import bcrypt
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "campus-service" / "data"

load_dotenv(PROJECT_ROOT / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "campus_qa"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "options": "-c lc_messages=C",
}


def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding("UTF8")
    return conn


def load_json(filename):
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  [SKIP] 文件不存在: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def hash_password(plain):
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def ensure_schema(cur, conn):
    init_sql = PROJECT_ROOT / "data" / "init.sql"
    if not init_sql.exists():
        print(f"  [ERROR] 找不到 init.sql: {init_sql}")
        sys.exit(1)
    sql = init_sql.read_text(encoding="utf-8")
    # psycopg2 cursor.execute 不支持多条分号分隔的 SQL 一次性执行，需逐条拆分
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        try:
            cur.execute(stmt)
            conn.commit()  # 每条语句独立提交，避免 rollback 影响后续语句
        except Exception as e:
            conn.rollback()
            if "already exists" not in str(e).lower():
                raise
            # already exists 是预期错误（重复运行幂等），跳过即可
    print("  [OK] 已执行 init.sql（建表 + 扩展）")


def truncate_all(cur):
    tables = [
        "campus.token_blacklist",
        "campus.student_schedule",
        "campus.repair_orders",
        "campus.scholarship_records",
        "campus.notices",
        "campus.schedules",
        "campus.students",
        "campus.admins",
    ]
    for t in tables:
        cur.execute(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE")
    print("  [OK] 已清空 campus schema 所有表")


def import_admins(cur, data):
    if data is None:
        return {}
    id_map = {}
    for item in data:
        cur.execute(
            "INSERT INTO campus.admins (username, name, password_hash, phone, email) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (item["username"], item["name"], hash_password(item["password"]),
             item.get("phone"), item.get("email")),
        )
        id_map[item["username"]] = cur.fetchone()[0]
    print(f"  [OK] 管理员: {len(data)} 条")
    return id_map


def import_students(cur, data):
    if data is None:
        return {}
    id_map = {}
    for item in data:
        cur.execute(
            "INSERT INTO campus.students "
            "(student_id, name, password_hash, gender, department, major, phone, email, "
            " birth_date, enrollment_year, dorm_building, dorm_room) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (item["student_id"], item["name"], hash_password(item["password"]),
             item.get("gender"), item.get("department"), item.get("major"),
             item.get("phone"), item.get("email"), item.get("birth_date"),
             item.get("enrollment_year"), item.get("dorm_building"), item.get("dorm_room")),
        )
        id_map[item["student_id"]] = cur.fetchone()[0]
    print(f"  [OK] 学生: {len(data)} 条")
    return id_map


def import_schedules(cur, data, admin_map):
    if data is None:
        return {}
    id_map = {}
    for item in data:
        admin_id = admin_map.get(item.get("created_by_username"))
        cur.execute(
            "INSERT INTO campus.schedules "
            "(course_name, teacher, weekday, start_period, end_period, location, "
            " start_week, end_week, semester, created_by) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (item["course_name"], item.get("teacher"), item["weekday"],
             item["start_period"], item["end_period"], item.get("location"),
             item.get("start_week", 1), item.get("end_week", 16),
             item.get("semester", "2025-2026-2"), admin_id),
        )
        id_map[item["course_name"]] = cur.fetchone()[0]
    print(f"  [OK] 课表: {len(data)} 条")
    return id_map


def import_student_schedule(cur, data, student_map, schedule_map):
    if data is None:
        return
    count = 0
    for item in data:
        sid = student_map.get(item["student_id"])
        if sid is None:
            print(f"  [WARN] 学生 {item['student_id']} 不存在，跳过选课")
            continue
        for course_name in item.get("courses", []):
            cid = schedule_map.get(course_name)
            if cid is None:
                print(f"  [WARN] 课程 {course_name} 不存在，跳过")
                continue
            cur.execute(
                "INSERT INTO campus.student_schedule (student_id, schedule_id) "
                "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (sid, cid),
            )
            count += 1
    print(f"  [OK] 学生选课关联: {count} 条")


def import_repair_orders(cur, data, student_map):
    if data is None:
        return
    for item in data:
        sid = student_map.get(item["student_id"])
        if sid is None:
            print(f"  [WARN] 学生 {item['student_id']} 不存在，跳过报修")
            continue
        cur.execute(
            "INSERT INTO campus.repair_orders "
            "(student_id, description, location, contact_phone, status, handler, "
            " handle_note, submitted_at, processed_at, completed_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (sid, item["description"], item.get("location"), item.get("contact_phone"),
             item.get("status", "pending"), item.get("handler"), item.get("handle_note"),
             item.get("submitted_at"), item.get("processed_at"), item.get("completed_at")),
        )
    print(f"  [OK] 宿舍报修: {len(data)} 条")


def import_scholarships(cur, data, student_map):
    if data is None:
        return
    for item in data:
        sid = student_map.get(item["student_id"])
        if sid is None:
            print(f"  [WARN] 学生 {item['student_id']} 不存在，跳过奖助记录")
            continue
        cur.execute(
            "INSERT INTO campus.scholarship_records "
            "(student_id, type, name, amount, status, semester, note) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (sid, item["type"], item["name"], item.get("amount"),
             item.get("status", "pending"), item.get("semester", "2025-2026-2"),
             item.get("note")),
        )
    print(f"  [OK] 奖助记录: {len(data)} 条")


def import_notices(cur, data, admin_map):
    if data is None:
        return
    for item in data:
        admin_id = admin_map.get(item.get("created_by_username"))
        cur.execute(
            "INSERT INTO campus.notices "
            "(title, content, category, publisher, published_at, updated_at, created_by) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (item["title"], item["content"], item.get("category", "general"),
             item.get("publisher"), item.get("published_at"),
             item.get("updated_at", item.get("published_at")), admin_id),
        )
    print(f"  [OK] 通知: {len(data)} 条")


def verify(cur):
    tables = [
        ("campus.admins", "管理员"),
        ("campus.students", "学生"),
        ("campus.schedules", "课表"),
        ("campus.student_schedule", "选课关联"),
        ("campus.repair_orders", "宿舍报修"),
        ("campus.scholarship_records", "奖助记录"),
        ("campus.notices", "通知"),
        ("campus.token_blacklist", "Token黑名单"),
    ]
    print("\n--- 导入结果验证 ---")
    for t, label in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {label}: {cur.fetchone()[0]} 条")


def main():
    print("=" * 60)
    print("  演示数据导入")
    print(f"  数据源: {DATA_DIR}")
    print(f"  目标: {DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print("=" * 60)

    conn = get_conn()
    cur = conn.cursor()

    try:
        ensure_schema(cur, conn)

        truncate_all(cur)
        conn.commit()

        admin_map = import_admins(cur, load_json("admins.json"))
        conn.commit()

        student_map = import_students(cur, load_json("students.json"))
        conn.commit()

        schedule_map = import_schedules(cur, load_json("schedules.json"), admin_map)
        conn.commit()

        import_student_schedule(cur, load_json("student_schedule.json"), student_map, schedule_map)
        conn.commit()

        import_repair_orders(cur, load_json("repair_orders.json"), student_map)
        conn.commit()

        import_scholarships(cur, load_json("scholarships.json"), student_map)
        conn.commit()

        import_notices(cur, load_json("notices.json"), admin_map)
        conn.commit()

        verify(cur)
        print("\n  导入完成。")
    except Exception as e:
        conn.rollback()
        print(f"\n  [ERROR] {type(e).__name__}: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
