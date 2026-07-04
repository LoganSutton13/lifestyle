from datetime import UTC, datetime
from uuid import UUID

import jwt
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import ConflictError, UnauthorizedError, ValidationError
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.core.tokens import generate_refresh_token, refresh_token_expires_at
from app.db.models.user import User
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.auth import AuthResponse, RegisterRequest, UserPublic

settings = get_settings()
REFRESH_COOKIE_NAME = "refresh_token"


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def _set_refresh_cookie(self, response: Response, token: str) -> None:
        samesite = "none" if settings.COOKIE_SECURE else "lax"
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=samesite,
            max_age=settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60,
            domain=settings.COOKIE_DOMAIN or None,
            path="/",
        )

    def _clear_refresh_cookie(self, response: Response) -> None:
        response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN or None)

    def _to_auth_response(self, user: User, access_token: str) -> AuthResponse:
        return AuthResponse(
            user=UserPublic(
                id=user.id,
                username=user.username,
                firstName=user.first_name,
                lastName=user.last_name,
                role=user.role,
                avatarKey=user.avatar_key,
                timezone=user.timezone,
            ),
            accessToken=access_token,
        )

    async def _issue_tokens(self, user: User, response: Response, user_agent: str | None = None) -> AuthResponse:
        access_token = create_access_token(user.id, user.role)
        refresh_token = generate_refresh_token()
        await self.refresh_tokens.create(
            user_id=user.id,
            token=refresh_token,
            expires_at=refresh_token_expires_at(),
            user_agent=user_agent,
        )
        self._set_refresh_cookie(response, refresh_token)
        return self._to_auth_response(user, access_token)

    async def register(self, data: RegisterRequest, response: Response) -> AuthResponse:
        if await self.users.username_exists(data.username):
            raise ConflictError("Username already exists")
        user = User(
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            password_hash=hash_password(data.password),
            role="client",
            timezone=data.timezone,
        )
        await self.users.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return await self._issue_tokens(user, response)

    async def login(self, username: str, password: str, response: Response, user_agent: str | None = None) -> AuthResponse:
        user = await self.users.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid username or password")
        return await self._issue_tokens(user, response, user_agent)

    async def refresh(self, refresh_token: str | None, response: Response) -> str:
        if not refresh_token:
            raise UnauthorizedError("Refresh token missing")
        stored = await self.refresh_tokens.get_valid_by_token(refresh_token)
        if not stored:
            raise UnauthorizedError("Invalid refresh token")
        user = await self.users.get_by_id(stored.user_id)
        if not user:
            raise UnauthorizedError("User not found")
        await self.refresh_tokens.revoke(stored)
        new_refresh = generate_refresh_token()
        await self.refresh_tokens.create(
            user_id=user.id,
            token=new_refresh,
            expires_at=refresh_token_expires_at(),
        )
        self._set_refresh_cookie(response, new_refresh)
        await self.db.commit()
        return create_access_token(user.id, user.role)

    async def logout(self, refresh_token: str | None, response: Response) -> None:
        if refresh_token:
            stored = await self.refresh_tokens.get_valid_by_token(refresh_token)
            if stored:
                await self.refresh_tokens.revoke(stored)
                await self.db.commit()
        self._clear_refresh_cookie(response)

    async def get_user_from_access_token(self, token: str) -> User:
        try:
            from app.core.security import decode_access_token

            payload = decode_access_token(token)
            user_id = UUID(payload["sub"])
        except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
            raise UnauthorizedError("Invalid access token") from exc
        user = await self.users.get_by_id(user_id)
        if not user:
            raise UnauthorizedError("User not found")
        return user
