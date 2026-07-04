from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import assert_coach_has_client, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.checklist import ChecklistHistoryResponse, DailyNotesListResponse
from app.schemas.coach import (
    AddClientRequest,
    ClientSearchResponse,
    CoachClientListResponse,
    CoachTaskListResponse,
    TaskCreateRequest,
    TaskUpdateRequest,
    CoachTaskItem,
)
from app.schemas.meals import MealCreateRequest, MealItem, MealListResponse, MealUpdateRequest
from app.schemas.measurements import MeasurementGraphResponse, MeasurementTypesListResponse
from app.services.checklist_service import ChecklistService
from app.services.coach_service import CoachService
from app.services.meal_service import MealService
from app.services.measurement_service import MeasurementService

router = APIRouter()


@router.get("/clients", response_model=CoachClientListResponse)
async def list_clients(
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50, alias="pageSize"),
) -> CoachClientListResponse:
    service = CoachService(db)
    return await service.list_clients(current_user.id, search or None, page, page_size)


@router.get("/client-search", response_model=ClientSearchResponse)
async def search_clients(
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    query: str = Query(min_length=1),
) -> ClientSearchResponse:
    service = CoachService(db)
    return await service.search_clients(current_user.id, query)


@router.post("/clients", status_code=204)
async def add_client(
    data: AddClientRequest,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = CoachService(db)
    await service.add_client(current_user.id, data)


@router.delete("/clients/{client_id}", status_code=204)
async def remove_client(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = CoachService(db)
    await service.remove_client(current_user.id, client_id)


@router.get("/clients/{client_id}/meals", response_model=MealListResponse)
async def list_client_meals(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50, alias="pageSize"),
    category: str | None = None,
) -> MealListResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = MealService(db)
    return await service.list_coach_client_meals(current_user.id, client_id, category, page, page_size)


@router.post("/clients/{client_id}/meals", response_model=MealItem, status_code=201)
async def create_client_meal(
    client_id: UUID,
    data: MealCreateRequest,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MealItem:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = MealService(db)
    return await service.create_meal_for_client(current_user.id, client_id, data)


@router.patch("/clients/{client_id}/meals/{meal_id}", response_model=MealItem)
async def update_client_meal(
    client_id: UUID,
    meal_id: UUID,
    data: MealUpdateRequest,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MealItem:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = MealService(db)
    return await service.update_meal(current_user.id, client_id, meal_id, data)


@router.delete("/clients/{client_id}/meals/{meal_id}", status_code=204)
async def delete_client_meal(
    client_id: UUID,
    meal_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = MealService(db)
    await service.delete_meal(current_user.id, meal_id)


@router.get("/clients/{client_id}/tasks", response_model=CoachTaskListResponse)
async def list_client_tasks(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    active: bool = True,
) -> CoachTaskListResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = ChecklistService(db)
    return await service.list_coach_tasks(current_user.id, client_id, active)


@router.post("/clients/{client_id}/tasks", response_model=CoachTaskItem, status_code=201)
async def create_client_task(
    client_id: UUID,
    data: TaskCreateRequest,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CoachTaskItem:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = ChecklistService(db)
    return await service.create_task(current_user.id, client_id, data)


@router.patch("/clients/{client_id}/tasks/{task_id}", response_model=CoachTaskItem)
async def update_client_task(
    client_id: UUID,
    task_id: UUID,
    data: TaskUpdateRequest,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CoachTaskItem:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = ChecklistService(db)
    return await service.update_task(current_user.id, client_id, task_id, data)


@router.delete("/clients/{client_id}/tasks/{task_id}", status_code=204)
async def delete_client_task(
    client_id: UUID,
    task_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = ChecklistService(db)
    await service.delete_task(current_user.id, client_id, task_id)


@router.get("/clients/{client_id}/measurement-types", response_model=MeasurementTypesListResponse)
async def list_client_measurement_types(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeasurementTypesListResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = MeasurementService(db)
    return await service.list_types()


@router.get("/clients/{client_id}/measurements", response_model=MeasurementGraphResponse)
async def get_client_measurements(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    type_key: str = Query(alias="typeKey"),
    start_date: date | None = Query(default=None, alias="startDate"),
    end_date: date | None = Query(default=None, alias="endDate"),
    unit_key: str | None = Query(default=None, alias="unitKey"),
) -> MeasurementGraphResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = MeasurementService(db)
    return await service.get_graph(client_id, type_key, start_date, end_date, unit_key)


@router.get("/clients/{client_id}/checklist-history", response_model=ChecklistHistoryResponse)
async def get_checklist_history(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: date = Query(alias="startDate"),
    end_date: date = Query(alias="endDate"),
) -> ChecklistHistoryResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = ChecklistService(db)
    return await service.checklist_history(client_id, start_date, end_date)


@router.get("/clients/{client_id}/daily-notes", response_model=DailyNotesListResponse)
async def get_daily_notes(
    client_id: UUID,
    current_user: Annotated[User, Depends(require_roles("coach"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: date = Query(alias="startDate"),
    end_date: date = Query(alias="endDate"),
) -> DailyNotesListResponse:
    await assert_coach_has_client(db, current_user.id, client_id)
    service = ChecklistService(db)
    return await service.list_daily_notes(client_id, start_date, end_date)
