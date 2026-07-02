from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timezone

from ..models.admin import Admin
from ..models.student import Student
from ..models.token_blacklist import TokenBlacklist
from ..utils.security import verify_password, hash_password, create_token
from ..utils.exceptions import NotFound, BadRequest


def login(db: Session, username: str, password: str, role: str):
    if role == "admin":
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            raise BadRequest("管理员账号不存在")
        if not verify_password(password, admin.password_hash):
            raise BadRequest("密码错误")
        token = create_token(sub=admin.username, role="admin", db_id=admin.id)
        return {
            "token": token,
            "user": {"role": "admin", "username": admin.username, "name": admin.name},
        }

    student = db.query(Student).filter(Student.student_id == username).first()
    if not student:
        raise BadRequest("学号不存在")
    if not verify_password(password, student.password_hash):
        raise BadRequest("密码错误")
    token = create_token(sub=student.student_id, role="student", db_id=student.id)
    return {
        "token": token,
        "user": {"role": "student", "username": student.student_id, "name": student.name},
    }


def get_me(db: Session, payload: dict):
    role = payload["role"]
    db_id = payload["db_id"]
    if role == "admin":
        user = db.query(Admin).filter(Admin.id == db_id).first()
        if not user:
            raise NotFound("用户")
        return {"role": "admin", "username": user.username, "name": user.name, "phone": user.phone, "email": user.email}
    else:
        user = db.query(Student).filter(Student.id == db_id).first()
        if not user:
            raise NotFound("用户")
        return {
            "role": "student",
            "student_id": user.student_id,
            "name": user.name,
            "gender": user.gender,
            "department": user.department,
            "major": user.major,
            "phone": user.phone,
            "email": user.email,
            "birth_date": str(user.birth_date) if user.birth_date else None,
            "enrollment_year": user.enrollment_year,
            "dorm_building": user.dorm_building,
            "dorm_room": user.dorm_room,
        }


def change_password(db: Session, payload: dict, old_password: str, new_password: str):
    role = payload["role"]
    db_id = payload["db_id"]
    if role == "admin":
        user = db.query(Admin).filter(Admin.id == db_id).first()
    else:
        user = db.query(Student).filter(Student.id == db_id).first()

    if not user:
        raise NotFound("用户")
    if not verify_password(old_password, user.password_hash):
        raise BadRequest("旧密码错误")

    user.password_hash = hash_password(new_password)
    db.commit()

    # 将当前 token 加入黑名单，强制重新登录
    jti = payload.get("jti")
    if jti:
        existing = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
        if not existing:
            entry = TokenBlacklist(
                jti=jti,
                user_sub=payload.get("sub", ""),
                expires_at=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc),
            )
            db.add(entry)
            db.commit()


def logout(db: Session, payload: dict):
    jti = payload.get("jti")
    if not jti:
        return
    existing = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    if existing:
        return
    entry = TokenBlacklist(
        jti=jti,
        user_sub=payload.get("sub", ""),
        expires_at=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc),
    )
    db.add(entry)
    db.commit()


def is_token_blacklisted(db: Session, jti: str) -> bool:
    if not jti:
        return False
    return db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first() is not None
