from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.meals import MealListResponse
from app.services.meal_service import MealService

router = APIRouter()


@router.get("", response_model=MealListResponse)
async def list_my_meals(
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50, alias="pageSize"),
    category: str | None = None,
) -> MealListResponse:
    service = MealService(db)
    return await service.list_client_meals(current_user.id, category, page, page_size)
