from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MealItem(BaseModel):
    id: UUID
    name: str
    category: str
    category_label: str = Field(alias="categoryLabel")
    description: str
    assigned_at: datetime = Field(alias="assignedAt")

    model_config = {"populate_by_name": True}


class MealListResponse(BaseModel):
    items: list[MealItem]
    page: int
    page_size: int = Field(alias="pageSize")
    total: int
    has_next_page: bool = Field(alias="hasNextPage")

    model_config = {"populate_by_name": True}


class MealCreateRequest(BaseModel):
    name: str
    category: str
    description: str = ""


class MealUpdateRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
