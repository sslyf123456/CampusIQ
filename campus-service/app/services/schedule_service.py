from sqlalchemy.orm import Session

from ..models.schedule import Schedule
from ..models.student import Student
from ..utils.exceptions import NotFound, BadRequest
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate


def list_schedules(db: Session, page: int = 1, page_size: int = 50, semester: str = ""):
    q = db.query(Schedule)
    if semester:
        q = q.filter(Schedule.semester == semester)
    total = q.count()
    items = q.order_by(Schedule.weekday, Schedule.start_period).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": items, "total": total, "page": page, "page_size": page_size}


def get_my_schedules(db: Session, student_db_id: int):
    student = db.query(Student).filter(Student.id == student_db_id).first()
    if not student:
        raise NotFound("学生")
    return student.schedules


def get_schedule(db: Session, schedule_id: int):
    s = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not s:
        raise NotFound("课程")
    return s


def create_schedule(db: Session, data: ScheduleCreate, admin_id: int):
    s = Schedule(**data.model_dump(), created_by=admin_id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_schedule(db: Session, schedule_id: int, data: ScheduleUpdate):
    s = get_schedule(db, schedule_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


def delete_schedule(db: Session, schedule_id: int):
    s = get_schedule(db, schedule_id)
    db.delete(s)
    db.commit()


def add_students_to_schedule(db: Session, schedule_id: int, student_ids: list[str]):
    s = get_schedule(db, schedule_id)
    for sid in student_ids:
        student = db.query(Student).filter(Student.student_id == sid).first()
        if not student:
            raise NotFound(f"学生 {sid}")
        if student not in s.students:
            s.students.append(student)
    db.commit()


def remove_student_from_schedule(db: Session, schedule_id: int, student_id: str):
    s = get_schedule(db, schedule_id)
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise NotFound(f"学生 {student_id}")
    if student not in s.students:
        raise BadRequest(f"学生 {student_id} 已移除此课程")
    s.students.remove(student)
    db.commit()
