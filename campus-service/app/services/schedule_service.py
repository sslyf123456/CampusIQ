from sqlalchemy.orm import Session

from ..models.schedule import Schedule, student_schedule
from ..models.student import Student
from ..utils.exceptions import NotFound, BadRequest
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate


def list_schedules(db: Session, page: int = 1, page_size: int = 50, semester: str = ""):
    q = db.query(Schedule)
    if semester:
        q = q.filter(Schedule.semester == semester)
    total = q.count()
    # 排序：学期降序 -> 周几升序 -> 开始节次升序 -> 结束节次升序 -> ID升序
    items = (
        q.order_by(
            Schedule.semester.desc(),
            Schedule.weekday.asc(),
            Schedule.start_period.asc(),
            Schedule.end_period.asc(),
            Schedule.id.asc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"data": items, "total": total, "page": page, "page_size": page_size}


def get_my_schedules(db: Session, student_db_id: int, semester: str = ""):
    student = db.query(Student).filter(Student.id == student_db_id).first()
    if not student:
        raise NotFound("学生")
    # 显式 join 关联表查询，与 list_schedules 保持一致的 DB 层排序
    q = (
        db.query(Schedule)
        .join(student_schedule, student_schedule.c.schedule_id == Schedule.id)
        .filter(student_schedule.c.student_id == student_db_id)
    )
    if semester:
        q = q.filter(Schedule.semester == semester)
    return (
        q.order_by(
            Schedule.semester.desc(),
            Schedule.weekday.asc(),
            Schedule.start_period.asc(),
            Schedule.end_period.asc(),
            Schedule.id.asc(),
        )
        .all()
    )


def get_all_semesters(db: Session) -> list[str]:
    """返回所有不重复的学期列表，按降序排列。"""
    rows = db.query(Schedule.semester).distinct().all()
    return sorted([r[0] for r in rows], reverse=True)


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


def get_schedule_students(db: Session, schedule_id: int):
    s = get_schedule(db, schedule_id)
    return s.students
