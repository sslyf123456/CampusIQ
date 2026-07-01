from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, require_admin
from ..schemas.notice import NoticeCreate, NoticeUpdate, NoticeOut
from ..services import notice_service
from ..utils.response import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/api/campus/notices", tags=["校园通知"])


@router.get("", response_model=PaginatedResponse[NoticeOut])
def list_notices(
    keyword: str = Query("", max_length=255),
    category: str = Query("", max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notice_service.list_notices(db, keyword, category, page, page_size)


@router.get("/{notice_id}", response_model=NoticeOut)
def get_notice(
    notice_id: int,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notice_service.get_notice(db, notice_id)


@router.post("", status_code=201, response_model=NoticeOut)
def create_notice(
    data: NoticeCreate,
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return notice_service.create_notice(db, data, admin["db_id"])


@router.put("/{notice_id}", response_model=NoticeOut)
def update_notice(
    notice_id: int,
    data: NoticeUpdate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return notice_service.update_notice(db, notice_id, data)


@router.delete("/{notice_id}", response_model=MessageResponse)
def delete_notice(
    notice_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    notice_service.delete_notice(db, notice_id)
    return {"detail": "删除成功"}
