from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..schemas.schedule import ScheduleOut
from ..schemas.repair_order import RepairOrderOut
from ..schemas.scholarship import ScholarshipOut
from ..schemas.notice import NoticeOut
from ..services import schedule_service, repair_service, scholarship_service, notice_service

router = APIRouter(prefix="/api/campus/internal", tags=["内部接口"])


@router.get("/schedule")
def internal_schedule(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "student":
        return {"data": []}
    courses = schedule_service.get_my_schedules(db, current_user["db_id"])
    courses_out = [ScheduleOut.model_validate(c).model_dump() for c in courses]
    return {"data": courses_out}


@router.get("/repair")
def internal_repair(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "student":
        return {"data": []}
    result = repair_service.list_repair_orders(db, student_db_id=current_user["db_id"])
    items_out = [RepairOrderOut.model_validate(r).model_dump() for r in result["data"]]
    return {"data": items_out}


@router.get("/scholarship")
def internal_scholarship(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "student":
        return {"data": []}
    result = scholarship_service.list_scholarships(db, student_db_id=current_user["db_id"])
    items_out = [ScholarshipOut.model_validate(r).model_dump() for r in result["data"]]
    return {"data": items_out}


@router.get("/notices")
def internal_notices(
    keyword: str = Query("", max_length=255),
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = notice_service.list_notices(db, keyword=keyword, page_size=10)
    items_out = [NoticeOut.model_validate(n).model_dump() for n in result["data"]]
    return {"data": items_out}
