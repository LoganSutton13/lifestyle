from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.admin import (
    AdminDeleteUserRequest,
    AdminStatsResponse,
    AdminUserListResponse,
    CreateCoachRequest,
    RoleUpdateRequest,
)
from app.schemas.auth import UserPublicWithCreated
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminStatsResponse:
    service = AdminService(db)
    return await service.get_stats()


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    role: str | None = None,
    search: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50, alias="pageSize"),
) -> AdminUserListResponse:
    service = AdminService(db)
    return await service.list_users(role, search or None, page, page_size)


@router.post("/coaches", response_model=UserPublicWithCreated, status_code=201)
async def create_coach(
    data: CreateCoachRequest,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserPublicWithCreated:
    service = AdminService(db)
    return await service.create_coach(data)


@router.patch("/users/{user_id}/role", response_model=UserPublicWithCreated)
async def update_user_role(
    user_id: UUID,
    data: RoleUpdateRequest,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserPublicWithCreated:
    if data.role != "coach":
        from app.api.error_handlers import ValidationError
        raise ValidationError("Only client to coach elevation is allowed")
    service = AdminService(db)
    return await service.elevate_to_coach(user_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    data: AdminDeleteUserRequest,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = AdminService(db)
    await service.delete_user(current_user.id, user_id, data)
