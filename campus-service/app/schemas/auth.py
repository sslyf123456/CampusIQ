from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=32, description="学号或管理员用户名")
    password: str = Field(..., min_length=1, max_length=64)


class LoginUserInfo(BaseModel):
    role: str
    username: str
    name: str


class LoginResponse(BaseModel):
    token: str
    user: LoginUserInfo


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=64)
