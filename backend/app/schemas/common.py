from typing import Any

from pydantic import BaseModel, Field


class AppError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: AppError


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10


class PaginatedResponse(BaseModel):
    page: int
    page_size: int
    total: int
    has_next_page: bool
