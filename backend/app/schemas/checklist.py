from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChecklistTask(BaseModel):
    id: UUID
    title: str
    description: str
    completed: bool


class DailyNoteInfo(BaseModel):
    body: str
    updated_at: datetime | None = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class ChecklistResponse(BaseModel):
    date: date
    tasks: list[ChecklistTask]
    note: DailyNoteInfo


class TaskCompletionRequest(BaseModel):
    date: date
    completed: bool


class DailyNoteRequest(BaseModel):
    date: date
    body: str


class ChecklistHistoryDay(BaseModel):
    date: date
    total_tasks: int = Field(alias="totalTasks")
    completed_tasks: int = Field(alias="completedTasks")

    model_config = {"populate_by_name": True}


class ChecklistHistoryResponse(BaseModel):
    items: list[ChecklistHistoryDay]


class DailyNotesListItem(BaseModel):
    date: date
    body: str
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class DailyNotesListResponse(BaseModel):
    items: list[DailyNotesListItem]
