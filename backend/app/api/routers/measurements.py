from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.measurements import (
    MeasurementCreateRequest,
    MeasurementGraphResponse,
    MeasurementPoint,
    MeasurementTypesListResponse,
)
from app.services.measurement_service import MeasurementService

router = APIRouter()


@router.get("/measurement-types", response_model=MeasurementTypesListResponse)
async def list_measurement_types(
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeasurementTypesListResponse:
    service = MeasurementService(db)
    return await service.list_types()


@router.get("/measurements", response_model=MeasurementGraphResponse)
async def get_measurements(
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    type_key: str = Query(alias="typeKey"),
    start_date: date | None = Query(default=None, alias="startDate"),
    end_date: date | None = Query(default=None, alias="endDate"),
    unit_key: str | None = Query(default=None, alias="unitKey"),
) -> MeasurementGraphResponse:
    service = MeasurementService(db)
    return await service.get_graph(
        current_user.id, type_key, start_date, end_date, unit_key, current_user.timezone
    )


@router.post("/measurements", response_model=MeasurementPoint, status_code=201)
async def create_measurement(
    data: MeasurementCreateRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeasurementPoint:
    service = MeasurementService(db)
    return await service.create_record(current_user.id, data)
