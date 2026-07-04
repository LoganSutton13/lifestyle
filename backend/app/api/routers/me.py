from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    ProfileUpdateRequest,
    UserPublic,
)
from app.services.user_service import UserService

router = APIRouter()


@router.put("", response_model=UserPublic)
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserPublic:
    service = UserService(db)
    return await service.update_profile(current_user.id, data)


@router.post("/change-password", status_code=204)
async def change_password(
    data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = UserService(db)
    await service.change_password(current_user.id, data)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    data: DeleteAccountRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = UserService(db)
    await service.delete_self(current_user.id, data)
