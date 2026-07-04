from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.checklist import (
    ChecklistResponse,
    DailyNoteInfo,
    DailyNoteRequest,
    TaskCompletionRequest,
)
from app.services.checklist_service import ChecklistService

router = APIRouter()


@router.get("/checklist", response_model=ChecklistResponse)
async def get_checklist(
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    target_date: date | None = Query(default=None, alias="date"),
) -> ChecklistResponse:
    service = ChecklistService(db)
    return await service.get_checklist(current_user.id, target_date or date.today())


@router.patch("/checklist/{task_id}/completion", status_code=204)
async def update_task_completion(
    task_id: UUID,
    data: TaskCompletionRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = ChecklistService(db)
    await service.set_completion(current_user.id, task_id, data)


@router.put("/daily-note", response_model=DailyNoteInfo)
async def save_daily_note(
    data: DailyNoteRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DailyNoteInfo:
    service = ChecklistService(db)
    return await service.save_daily_note(current_user.id, data)
