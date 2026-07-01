import time

import bcrypt


def _jwt():
    import jwt as _jwt_module
    return _jwt_module


from ..config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(sub: str, role: str, db_id: int) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "role": role,
        "db_id": db_id,
        "iat": now,
        "exp": now + settings.JWT_EXPIRE_HOURS * 3600,
    }
    return _jwt().encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return _jwt().decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
