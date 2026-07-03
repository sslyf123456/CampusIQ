from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_admin
from ..schemas.student import StudentCreate, StudentUpdate, StudentOut
from ..schemas.schedule import ScheduleOut
from ..services import student_service
from ..utils.response import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/api/campus/students", tags=["学生管理"])


@router.get("", response_model=PaginatedResponse[StudentOut])
def list_students(
    keyword: str = Query("", max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.list_students(db, keyword, page, page_size)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: str,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.get_student(db, student_id)


@router.post("", status_code=201, response_model=StudentOut)
def create_student(
    data: StudentCreate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.create_student(db, data)


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: str,
    data: StudentUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.update_student(db, student_id, data)


@router.delete("/{student_id}", response_model=MessageResponse)
def delete_student(
    student_id: str,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    student_service.delete_student(db, student_id)
    return {"detail": "删除成功"}


@router.get("/{student_id}/schedules", response_model=list[ScheduleOut])
def get_student_schedules(
    student_id: str,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.get_student_schedules(db, student_id)
