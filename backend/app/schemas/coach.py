from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CoachClientSummary(BaseModel):
    id: UUID
    username: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    avatar_key: str = Field(alias="avatarKey")
    latest_body_weight: Decimal | None = Field(default=None, alias="latestBodyWeight")
    today_completed_tasks: int = Field(default=0, alias="todayCompletedTasks")
    today_total_tasks: int = Field(default=0, alias="todayTotalTasks")

    model_config = {"populate_by_name": True}


class CoachClientProfile(BaseModel):
    id: UUID
    username: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    timezone: str

    model_config = {"populate_by_name": True}


class CoachClientListResponse(BaseModel):
    items: list[CoachClientSummary]
    page: int
    page_size: int = Field(alias="pageSize")
    total: int
    has_next_page: bool = Field(alias="hasNextPage")

    model_config = {"populate_by_name": True}


class ClientSearchResult(BaseModel):
    id: UUID
    username: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    avatar_key: str = Field(alias="avatarKey")

    model_config = {"populate_by_name": True}


class ClientSearchResponse(BaseModel):
    items: list[ClientSearchResult]


class AddClientRequest(BaseModel):
    client_id: UUID = Field(alias="clientId")

    model_config = {"populate_by_name": True}


class TaskCreateRequest(BaseModel):
    title: str
    description: str = ""
    active_from: date = Field(alias="activeFrom")
    active_until: date | None = Field(default=None, alias="activeUntil")
    recurrence_frequency: str = Field(default="daily", alias="recurrenceFrequency")
    recurrence_interval: int = Field(default=1, alias="recurrenceInterval")
    recurrence_days: list[int] = Field(default_factory=list, alias="recurrenceDays")

    model_config = {"populate_by_name": True}


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    active_from: date | None = Field(default=None, alias="activeFrom")
    active_until: date | None = Field(default=None, alias="activeUntil")
    recurrence_frequency: str | None = Field(default=None, alias="recurrenceFrequency")
    recurrence_interval: int | None = Field(default=None, alias="recurrenceInterval")
    recurrence_days: list[int] | None = Field(default=None, alias="recurrenceDays")

    model_config = {"populate_by_name": True}


class CoachTaskItem(BaseModel):
    id: UUID
    title: str
    description: str
    active_from: date = Field(alias="activeFrom")
    active_until: date | None = Field(alias="activeUntil")
    recurrence_frequency: str = Field(alias="recurrenceFrequency")
    recurrence_interval: int = Field(alias="recurrenceInterval")
    recurrence_days: list[int] = Field(alias="recurrenceDays")
    archived_at: datetime | None = Field(alias="archivedAt")

    model_config = {"populate_by_name": True}


class CoachTaskListResponse(BaseModel):
    items: list[CoachTaskItem]
