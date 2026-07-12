from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import assert_coach_has_client, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.coach_workouts import (
    AssignmentCreateRequest,
    TemplateCreateRequest,
    TemplateDetailResponse,
    TemplateDraftUpdateRequest,
    TemplateListResponse,
    TemplateVersionResponse,
)
from app.schemas.workouts import AssignmentListItem, AssignmentListResponse, WorkoutHistoryListResponse, WorkoutSessionDetailResponse
from app.services.workout_template_service import WorkoutTemplateService

router = APIRouter()


@router.get("/workout-templates", response_model=TemplateListResponse)
async def list_workout_templates(
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_archived: bool = Query(default=False, alias="includeArchived"),
) -> TemplateListResponse:
    service = WorkoutTemplateService(db)
    return await service.list_templates(current_user.id, include_archived)


@router.post("/workout-templates", response_model=TemplateDetailResponse, status_code=201)
async def create_workout_template(
    data: TemplateCreateRequest,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TemplateDetailResponse:
    service = WorkoutTemplateService(db)
    return await service.create_template(current_user.id, data)


@router.get("/workout-templates/{template_id}", response_model=TemplateDetailResponse)
async def get_workout_template(
    template_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TemplateDetailResponse:
    service = WorkoutTemplateService(db)
    return await service.get_template(current_user.id, template_id)


@router.delete("/workout-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout_template(
    template_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = WorkoutTemplateService(db)
    await service.delete_template(current_user.id, template_id)


@router.post("/workout-templates/{template_id}/draft", response_model=TemplateVersionResponse)
async def create_workout_template_draft(
    template_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TemplateVersionResponse:
    service = WorkoutTemplateService(db)
    return await service.create_draft(current_user.id, template_id)


@router.put("/workout-template-versions/{version_id}", response_model=TemplateVersionResponse)
async def update_workout_template_version(
    version_id: UUID,
    data: TemplateDraftUpdateRequest,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TemplateVersionResponse:
    service = WorkoutTemplateService(db)
    return await service.update_draft(current_user.id, version_id, data)


@router.post("/workout-template-versions/{version_id}/publish", response_model=TemplateVersionResponse)
async def publish_workout_template_version(
    version_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TemplateVersionResponse:
    service = WorkoutTemplateService(db)
    return await service.publish_version(current_user.id, version_id)


@router.get("/clients/{client_id}/workout-assignments", response_model=AssignmentListResponse)
async def list_client_workout_assignments(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    page_size: int = Query(default=20, ge=1, le=50, alias="pageSize"),
) -> AssignmentListResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = WorkoutTemplateService(db)
    return await service.list_client_assignments(current_user.id, client_id, cursor, page_size)


@router.post("/clients/{client_id}/workout-assignments", response_model=AssignmentListItem, status_code=201)
async def create_client_workout_assignment(
    client_id: UUID,
    data: AssignmentCreateRequest,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignmentListItem:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = WorkoutTemplateService(db)
    return await service.create_assignment(current_user, client_id, data)


@router.post(
    "/clients/{client_id}/workout-assignments/{assignment_id}/cancel", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_client_workout_assignment(
    client_id: UUID,
    assignment_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = WorkoutTemplateService(db)
    await service.cancel_assignment(current_user.id, client_id, assignment_id)


@router.get("/clients/{client_id}/workouts", response_model=WorkoutHistoryListResponse)
async def list_client_workouts(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    page_size: int = Query(default=20, ge=1, le=50, alias="pageSize"),
) -> WorkoutHistoryListResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = WorkoutTemplateService(db)
    return await service.list_client_workouts(current_user.id, client_id, cursor, page_size)


@router.get("/clients/{client_id}/workouts/{session_id}", response_model=WorkoutSessionDetailResponse)
async def get_client_workout_detail(
    client_id: UUID,
    session_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkoutSessionDetailResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = WorkoutTemplateService(db)
    return await service.get_client_workout_detail(current_user.id, client_id, session_id)
