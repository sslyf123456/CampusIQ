from sqlalchemy.orm import Session

from ..models.scholarship import ScholarshipRecord
from ..models.student import Student
from ..utils.exceptions import NotFound, Forbidden, BadRequest
from ..schemas.scholarship import ScholarshipCreate, ScholarshipUpdate, ScholarshipOut


def list_scholarships(db: Session, page: int = 1, page_size: int = 20, student_db_id: int = None, status: str = ""):
    q = db.query(ScholarshipRecord, Student.student_id, Student.name).join(
        Student, ScholarshipRecord.student_id == Student.id
    )
    if student_db_id:
        q = q.filter(ScholarshipRecord.student_id == student_db_id)
    if status:
        q = q.filter(ScholarshipRecord.status == status)
    total = q.count()
    rows = q.order_by(ScholarshipRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    # 组装：record 对象 + 学号 + 姓名
    items = []
    for record, sno, sname in rows:
        item = ScholarshipOut.model_validate(record).model_dump()
        item["student_no"] = sno
        item["student_name"] = sname
        items.append(item)
    return {"data": items, "total": total, "page": page, "page_size": page_size}


def get_scholarship(db: Session, record_id: int, student_db_id: int = None):
    record = db.query(ScholarshipRecord).filter(ScholarshipRecord.id == record_id).first()
    if not record:
        raise NotFound("奖助记录")
    if student_db_id and record.student_id != student_db_id:
        raise Forbidden("只能查看自己的奖助记录")
    return record


def create_scholarship(db: Session, data: ScholarshipCreate):
    student = db.query(Student).filter(Student.student_id == data.student_id).first()
    if not student:
        raise BadRequest(f"学号 {data.student_id} 不存在")
    record = ScholarshipRecord(
        student_id=student.id,
        type=data.type,
        name=data.name,
        amount=data.amount,
        status=data.status,
        semester=data.semester,
        note=data.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_scholarship(db: Session, record_id: int, data: ScholarshipUpdate):
    record = get_scholarship(db, record_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(record, k, v)
    db.commit()
    db.refresh(record)
    return record


def delete_scholarship(db: Session, record_id: int):
    record = get_scholarship(db, record_id)
    db.delete(record)
    db.commit()
