from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, require_admin
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate, AddStudentsRequest
from ..services import schedule_service

router = APIRouter(prefix="/api/campus/schedules", tags=["课表管理"])


@router.get("")
def list_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    semester: str = Query("", max_length=32),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "student":
        return {"data": schedule_service.get_my_schedules(db, current_user["db_id"])}
    return schedule_service.list_schedules(db, page, page_size, semester)


@router.get("/{schedule_id}")
def get_schedule(
    schedule_id: int,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return schedule_service.get_schedule(db, schedule_id)


@router.post("", status_code=201)
def create_schedule(
    data: ScheduleCreate,
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return schedule_service.create_schedule(db, data, admin["db_id"])


@router.put("/{schedule_id}")
def update_schedule(
    schedule_id: int,
    data: ScheduleUpdate,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return schedule_service.update_schedule(db, schedule_id, data)


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule_service.delete_schedule(db, schedule_id)
    return {"detail": "删除成功"}


@router.post("/{schedule_id}/students")
def add_students(
    schedule_id: int,
    data: AddStudentsRequest,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule_service.add_students_to_schedule(db, schedule_id, data.student_ids)
    return {"detail": "添加成功"}


@router.delete("/{schedule_id}/students/{student_id}")
def remove_student(
    schedule_id: int,
    student_id: str,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule_service.remove_student_from_schedule(db, schedule_id, student_id)
    return {"detail": "移除成功"}
