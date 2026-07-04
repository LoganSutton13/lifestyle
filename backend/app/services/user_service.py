from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from app.core.security import hash_password, verify_password
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.auth import ChangePasswordRequest, DeleteAccountRequest, ProfileUpdateRequest, UserPublic


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def to_public(self, user) -> UserPublic:
        return UserPublic(
            id=user.id,
            username=user.username,
            firstName=user.first_name,
            lastName=user.last_name,
            role=user.role,
            avatarKey=user.avatar_key,
            timezone=user.timezone,
        )

    async def update_profile(self, user_id: UUID, data: ProfileUpdateRequest) -> UserPublic:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if data.username and data.username != user.username:
            if await self.users.username_exists(data.username, exclude_id=user.id):
                raise ConflictError("Username already exists")
            user.username = data.username
        if data.first_name is not None:
            user.first_name = data.first_name
        if data.last_name is not None:
            user.last_name = data.last_name
        if data.timezone is not None:
            user.timezone = data.timezone
        if data.avatar_key is not None:
            user.avatar_key = data.avatar_key
        await self.db.commit()
        await self.db.refresh(user)
        return self.to_public(user)

    async def change_password(self, user_id: UUID, data: ChangePasswordRequest) -> None:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if not verify_password(data.current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect")
        user.password_hash = hash_password(data.new_password)
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.db.commit()

    async def delete_self(self, user_id: UUID, data: DeleteAccountRequest) -> None:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Password is incorrect")
        if user.role == "admin":
            admin_count = await self.users.count_by_role("admin")
            if admin_count <= 1:
                raise ValidationError("Cannot delete the last admin account")
        await self.audit_logs.log("user_self_delete", actor_user_id=user.id, target_user_id=user.id)
        await self.users.delete(user)
        await self.db.commit()
