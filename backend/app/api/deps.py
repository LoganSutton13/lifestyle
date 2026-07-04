from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import ForbiddenError, UnauthorizedError
from app.db.models.user import User
from app.db.session import get_db
from app.services.auth_service import REFRESH_COOKIE_NAME, AuthService
from app.services.coach_service import CoachService

security = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedError()
    auth_service = AuthService(db)
    return await auth_service.get_user_from_access_token(credentials.credentials)


def require_roles(*roles: str) -> Callable:
    async def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("Insufficient permissions")
        return current_user

    return dependency


async def assert_coach_has_client(db: AsyncSession, coach_id: UUID, client_id: UUID) -> None:
    coach_service = CoachService(db)
    await coach_service.assert_coach_has_client(coach_id, client_id)


def get_refresh_token(refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None) -> str | None:
    return refresh_token
