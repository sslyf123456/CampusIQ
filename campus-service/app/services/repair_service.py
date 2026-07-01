from datetime import datetime

from sqlalchemy.orm import Session

from ..models.repair_order import RepairOrder
from ..utils.exceptions import NotFound, Forbidden
from ..schemas.repair_order import RepairOrderCreate, RepairOrderUpdate


def list_repair_orders(db: Session, page: int = 1, page_size: int = 20, student_db_id: int = None, status: str = ""):
    q = db.query(RepairOrder)
    if student_db_id:
        q = q.filter(RepairOrder.student_id == student_db_id)
    if status:
        q = q.filter(RepairOrder.status == status)
    total = q.count()
    items = q.order_by(RepairOrder.submitted_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": items, "total": total, "page": page, "page_size": page_size}


def get_repair_order(db: Session, order_id: int, student_db_id: int = None):
    order = db.query(RepairOrder).filter(RepairOrder.id == order_id).first()
    if not order:
        raise NotFound("报修工单")
    if student_db_id and order.student_id != student_db_id:
        raise Forbidden("只能查看自己的报修工单")
    return order


def create_repair_order(db: Session, data: RepairOrderCreate, student_db_id: int):
    order = RepairOrder(
        student_id=student_db_id,
        description=data.description,
        location=data.location,
        contact_phone=data.contact_phone,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_repair_order(db: Session, order_id: int, data: RepairOrderUpdate):
    order = get_repair_order(db, order_id)
    order.status = data.status
    order.handler = data.handler
    order.handle_note = data.handle_note
    now = datetime.utcnow()
    if data.status == "processing" and not order.processed_at:
        order.processed_at = now
    elif data.status == "completed":
        order.completed_at = now
    db.commit()
    db.refresh(order)
    return order
