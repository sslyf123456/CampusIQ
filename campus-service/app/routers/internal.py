from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..dependencies import get_current_user
from ..schemas.schedule import ScheduleOut
from ..schemas.repair_order import RepairOrderOut
from ..schemas.scholarship import ScholarshipOut
from ..schemas.notice import NoticeOut
from ..schemas.student import StudentOut
from ..services import schedule_service, repair_service, scholarship_service, notice_service, student_service
from ..utils.exceptions import Forbidden

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campus/internal", tags=["内部接口"])


@router.get("/schedule")
def internal_schedule(
    semester: str = Query("", max_length=32),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "student":
        courses = schedule_service.get_my_schedules(db, current_user["db_id"], semester=semester)
        courses_out = [ScheduleOut.model_validate(c).model_dump() for c in courses]
        return {"data": courses_out}
    # 管理员返回所有课表（用 ScheduleOut 序列化，避免暴露 students/password_hash）
    result = schedule_service.list_schedules(db, 1, 100, semester=semester)
    courses_out = [ScheduleOut.model_validate(c).model_dump() for c in result["data"]]
    return {"data": courses_out}


@router.get("/repair")
def internal_repair(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "student":
        result = repair_service.list_repair_orders(db, student_db_id=current_user["db_id"])
        items_out = [RepairOrderOut.model_validate(r).model_dump() for r in result["data"]]
        return {"data": items_out}
    # 管理员返回所有报修订单
    result = repair_service.list_repair_orders(db)
    items_out = [RepairOrderOut.model_validate(r).model_dump() for r in result["data"]]
    return {"data": items_out}


@router.get("/scholarship")
def internal_scholarship(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "student":
        result = scholarship_service.list_scholarships(db, student_db_id=current_user["db_id"])
        items_out = [ScholarshipOut.model_validate(r).model_dump() for r in result["data"]]
        return {"data": items_out}
    # 管理员返回所有奖学金记录
    result = scholarship_service.list_scholarships(db)
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


@router.get("/students")
def internal_students(
    keyword: str = Query("", max_length=64),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise Forbidden("学生信息查询仅对管理员开放")
    result = student_service.list_students(db, keyword=keyword, page=1, page_size=100)
    items_out = [StudentOut.model_validate(s).model_dump() for s in result["data"]]
    return {"data": items_out, "total": result["total"]}
