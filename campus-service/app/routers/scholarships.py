from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, require_admin
from ..schemas.scholarship import ScholarshipCreate, ScholarshipUpdate, ScholarshipOut
from ..services import scholarship_service
from ..utils.response import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/api/campus/scholarships", tags=["奖助管理"])


@router.get("")
def list_scholarships(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query("", max_length=32),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "admin":
        return scholarship_service.list_scholarships(db, page, page_size, status=status)
    return scholarship_service.list_scholarships(db, page, page_size, student_db_id=current_user["db_id"], status=status)


@router.get("/{record_id}", response_model=ScholarshipOut)
def get_scholarship(
    record_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "admin":
        return scholarship_service.get_scholarship(db, record_id)
    return scholarship_service.get_scholarship(db, record_id, student_db_id=current_user["db_id"])


@router.post("", status_code=201, response_model=ScholarshipOut)
def create_scholarship(
    data: ScholarshipCreate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return scholarship_service.create_scholarship(db, data)


@router.put("/{record_id}", response_model=ScholarshipOut)
def update_scholarship(
    record_id: int,
    data: ScholarshipUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return scholarship_service.update_scholarship(db, record_id, data)


@router.delete("/{record_id}", response_model=MessageResponse)
def delete_scholarship(
    record_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    scholarship_service.delete_scholarship(db, record_id)
    return {"detail": "删除成功"}
