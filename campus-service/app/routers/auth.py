from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..schemas.auth import LoginRequest, ChangePasswordRequest, LoginResponse
from ..services.auth_service import login, get_me, change_password
from ..utils.response import MessageResponse

router = APIRouter(prefix="/api/campus/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse)
def login_endpoint(req: LoginRequest, db: Session = Depends(get_db)):
    return login(db, req.username, req.password)


@router.get("/me")
def me_endpoint(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_me(db, current_user)


@router.put("/password", response_model=MessageResponse)
def change_password_endpoint(
    req: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change_password(db, current_user, req.old_password, req.new_password)
    return {"detail": "密码修改成功"}
