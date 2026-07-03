from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, require_admin
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate, AddStudentsRequest, ScheduleOut
from ..schemas.student import StudentOut
from ..services import schedule_service
from ..utils.response import PaginatedResponse, DataResponse, MessageResponse

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
        courses = schedule_service.get_my_schedules(db, current_user["db_id"], semester)
        courses_out = [ScheduleOut.model_validate(c).model_dump() for c in courses]
        return {"data": courses_out}
    result = schedule_service.list_schedules(db, page, page_size, semester)
    courses_out = [ScheduleOut.model_validate(c).model_dump() for c in result["data"]]
    return {"data": courses_out, "total": result["total"], "page": result["page"], "page_size": result["page_size"]}


@router.get("/semesters", response_model=list[str])
def list_semesters(
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有不重复的学期列表（降序），用于前端筛选下拉框。"""
    return schedule_service.get_all_semesters(db)


@router.get("/{schedule_id}", response_model=ScheduleOut)
def get_schedule(
    schedule_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return schedule_service.get_schedule(db, schedule_id)


@router.post("", status_code=201, response_model=ScheduleOut)
def create_schedule(
    data: ScheduleCreate,
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return schedule_service.create_schedule(db, data, admin["db_id"])


@router.put("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: int,
    data: ScheduleUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return schedule_service.update_schedule(db, schedule_id, data)


@router.delete("/{schedule_id}", response_model=MessageResponse)
def delete_schedule(
    schedule_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule_service.delete_schedule(db, schedule_id)
    return {"detail": "删除成功"}


@router.post("/{schedule_id}/students", response_model=MessageResponse)
def add_students(
    schedule_id: int,
    data: AddStudentsRequest,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule_service.add_students_to_schedule(db, schedule_id, data.student_ids)
    return {"detail": "添加成功"}


@router.delete("/{schedule_id}/students/{student_id}", response_model=MessageResponse)
def remove_student(
    schedule_id: int,
    student_id: str,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule_service.remove_student_from_schedule(db, schedule_id, student_id)
    return {"detail": "移除成功"}


@router.get("/{schedule_id}/students", response_model=list[StudentOut])
def get_schedule_students(
    schedule_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return schedule_service.get_schedule_students(db, schedule_id)
