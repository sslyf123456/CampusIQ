from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .database import get_db
from .utils.security import decode_token
from .services.auth_service import is_token_blacklisted

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    if is_token_blacklisted(db, payload.get("jti", "")):
        raise HTTPException(status_code=401, detail="Token已失效，请重新登录")
    return payload


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def require_student(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="需要学生身份")
    return current_user
