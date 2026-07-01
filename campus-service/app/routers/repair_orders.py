from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, require_admin, require_student
from ..schemas.repair_order import RepairOrderCreate, RepairOrderUpdate
from ..services import repair_service

router = APIRouter(prefix="/api/campus/repair-orders", tags=["宿舍报修"])


@router.get("")
def list_repair_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query("", max_length=32),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "admin":
        return repair_service.list_repair_orders(db, page, page_size, status=status)
    return repair_service.list_repair_orders(db, page, page_size, student_db_id=current_user["db_id"], status=status)


@router.get("/{order_id}")
def get_repair_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "admin":
        return repair_service.get_repair_order(db, order_id)
    return repair_service.get_repair_order(db, order_id, student_db_id=current_user["db_id"])


@router.post("", status_code=201)
def create_repair_order(
    data: RepairOrderCreate,
    student: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    return repair_service.create_repair_order(db, data, student["db_id"])


@router.put("/{order_id}")
def update_repair_order(
    order_id: int,
    data: RepairOrderUpdate,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return repair_service.update_repair_order(db, order_id, data)
