from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_refresh_token
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    AccessTokenResponse,
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserPublic,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    data: RegisterRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    service = AuthService(db)
    return await service.register(data, response)


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    service = AuthService(db)
    user_agent = request.headers.get("user-agent")
    return await service.login(data.username, data.password, response, user_agent)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Depends(get_refresh_token)],
) -> AccessTokenResponse:
    service = AuthService(db)
    access_token = await service.refresh(refresh_token, response)
    return AccessTokenResponse(accessToken=access_token)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Depends(get_refresh_token)],
) -> None:
    service = AuthService(db)
    await service.logout(refresh_token, response)


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic(
        id=current_user.id,
        username=current_user.username,
        firstName=current_user.first_name,
        lastName=current_user.last_name,
        role=current_user.role,
        avatarKey=current_user.avatar_key,
        timezone=current_user.timezone,
    )
