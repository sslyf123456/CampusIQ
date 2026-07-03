from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models.student import Student
from ..models.schedule import Schedule, student_schedule
from ..utils.security import hash_password
from ..utils.exceptions import NotFound, BadRequest
from ..schemas.student import StudentCreate, StudentUpdate
from ..schemas.schedule import ScheduleOut


def list_students(db: Session, keyword: str = "", page: int = 1, page_size: int = 20):
    q = db.query(Student)
    if keyword:
        q = q.filter(
            or_(
                Student.student_id.ilike(f"%{keyword}%"),
                Student.name.ilike(f"%{keyword}%"),
                Student.department.ilike(f"%{keyword}%"),
            )
        )
    total = q.count()
    items = q.order_by(Student.student_id).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": items, "total": total, "page": page, "page_size": page_size}


def get_student(db: Session, student_id: str):
    s = db.query(Student).filter(Student.student_id == student_id).first()
    if not s:
        raise NotFound("学生")
    return s


def create_student(db: Session, data: StudentCreate):
    if db.query(Student).filter(Student.student_id == data.student_id).first():
        raise BadRequest(f"学号 {data.student_id} 已存在")
    s = Student(
        student_id=data.student_id,
        name=data.name,
        password_hash=hash_password(data.password),
        gender=data.gender,
        department=data.department,
        major=data.major,
        phone=data.phone,
        email=data.email,
        birth_date=data.birth_date,
        enrollment_year=data.enrollment_year,
        dorm_building=data.dorm_building,
        dorm_room=data.dorm_room,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_student(db: Session, student_id: str, data: StudentUpdate):
    s = get_student(db, student_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


def delete_student(db: Session, student_id: str):
    s = get_student(db, student_id)
    db.delete(s)
    db.commit()


def get_student_schedules(db: Session, student_id: str):
    s = get_student(db, student_id)
    courses = (
        db.query(Schedule)
        .join(student_schedule, student_schedule.c.schedule_id == Schedule.id)
        .filter(student_schedule.c.student_id == s.id)
        .order_by(
            Schedule.semester.desc(),
            Schedule.weekday.asc(),
            Schedule.start_period.asc(),
            Schedule.end_period.asc(),
            Schedule.id.asc(),
        )
        .all()
    )
    return courses
