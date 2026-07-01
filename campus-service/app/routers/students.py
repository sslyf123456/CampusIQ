from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_admin
from ..schemas.student import StudentCreate, StudentUpdate
from ..services import student_service

router = APIRouter(prefix="/api/campus/students", tags=["学生管理"])


@router.get("")
def list_students(
    keyword: str = Query("", max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.list_students(db, keyword, page, page_size)


@router.get("/{student_id}")
def get_student(
    student_id: str,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.get_student(db, student_id)


@router.post("", status_code=201)
def create_student(
    data: StudentCreate,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.create_student(db, data)


@router.put("/{student_id}")
def update_student(
    student_id: str,
    data: StudentUpdate,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return student_service.update_student(db, student_id, data)


@router.delete("/{student_id}")
def delete_student(
    student_id: str,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    student_service.delete_student(db, student_id)
    return {"detail": "删除成功"}
