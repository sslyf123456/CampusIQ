from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    page_size: int


class DataResponse(BaseModel, Generic[T]):
    data: T


class MessageResponse(BaseModel):
    detail: str
