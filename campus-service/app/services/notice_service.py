from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models.notice import Notice
from ..utils.exceptions import NotFound
from ..schemas.notice import NoticeCreate, NoticeUpdate


def list_notices(
    db: Session,
    keyword: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 20,
):
    q = db.query(Notice)
    if keyword:
        q = q.filter(
            or_(Notice.title.ilike(f"%{keyword}%"), Notice.content.ilike(f"%{keyword}%"))
        )
    if category:
        q = q.filter(Notice.category == category)
    total = q.count()
    items = q.order_by(Notice.published_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": items, "total": total, "page": page, "page_size": page_size}


def get_notice(db: Session, notice_id: int):
    n = db.query(Notice).filter(Notice.id == notice_id).first()
    if not n:
        raise NotFound("通知")
    return n


def create_notice(db: Session, data: NoticeCreate, admin_id: int):
    n = Notice(**data.model_dump(), created_by=admin_id)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def update_notice(db: Session, notice_id: int, data: NoticeUpdate):
    n = get_notice(db, notice_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(n, k, v)
    db.commit()
    db.refresh(n)
    return n


def delete_notice(db: Session, notice_id: int):
    n = get_notice(db, notice_id)
    db.delete(n)
    db.commit()
