from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..services import schedule_service, repair_service, scholarship_service, notice_service

router = APIRouter(prefix="/api/campus/internal", tags=["内部接口"])


@router.get("/schedule")
def internal_schedule(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "student":
        return {"data": []}
    return {"data": schedule_service.get_my_schedules(db, current_user["db_id"])}


@router.get("/repair")
def internal_repair(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "student":
        return {"data": []}
    return repair_service.list_repair_orders(db, student_db_id=current_user["db_id"])


@router.get("/scholarship")
def internal_scholarship(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "student":
        return {"data": []}
    return scholarship_service.list_scholarships(db, student_db_id=current_user["db_id"])


@router.get("/notices")
def internal_notices(
    keyword: str = Query("", max_length=255),
    _=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notice_service.list_notices(db, keyword=keyword, page_size=10)
