from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.exercises import (
    ExerciseCreateRequest,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseUpdateRequest,
)
from app.services.exercise_service import ExerciseService

router = APIRouter()


@router.get("", response_model=ExerciseListResponse)
async def search_exercises(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    query: str | None = None,
    equipment: str | None = None,
    muscle_group: str | None = Query(default=None, alias="muscleGroup"),
    include_archived: bool = Query(default=False, alias="includeArchived"),
    cursor: str | None = None,
    page_size: int = Query(default=30, ge=1, le=50, alias="pageSize"),
) -> ExerciseListResponse:
    service = ExerciseService(db)
    return await service.search(
        current_user, query, equipment, muscle_group, include_archived, cursor, page_size
    )


@router.post("", response_model=ExerciseResponse, status_code=201)
async def create_exercise(
    data: ExerciseCreateRequest,
    current_user: Annotated[User, Depends(require_roles("coach", "admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExerciseResponse:
    service = ExerciseService(db)
    return await service.create_exercise(current_user, data)


@router.patch("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: UUID,
    data: ExerciseUpdateRequest,
    current_user: Annotated[User, Depends(require_roles("coach", "admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExerciseResponse:
    service = ExerciseService(db)
    return await service.update_exercise(current_user, exercise_id, data)


@router.delete("/{exercise_id}", response_model=ExerciseResponse)
async def archive_exercise(
    exercise_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach", "admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExerciseResponse:
    service = ExerciseService(db)
    return await service.archive_exercise(current_user, exercise_id)


@router.post("/{exercise_id}/restore", response_model=ExerciseResponse)
async def restore_exercise(
    exercise_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExerciseResponse:
    service = ExerciseService(db)
    return await service.restore_exercise(current_user, exercise_id)
