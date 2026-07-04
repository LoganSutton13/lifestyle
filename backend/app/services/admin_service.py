from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from app.core.security import hash_password, verify_password
from app.db.models.user import User
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.users import UserRepository
from app.schemas.admin import (
    AdminDeleteUserRequest,
    AdminStatsResponse,
    AdminUserListResponse,
    CreateCoachRequest,
    RoleUpdateRequest,
)
from app.schemas.auth import UserPublicWithCreated


class AdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def _to_public_with_created(self, user: User) -> UserPublicWithCreated:
        return UserPublicWithCreated(
            id=user.id,
            username=user.username,
            firstName=user.first_name,
            lastName=user.last_name,
            role=user.role,
            avatarKey=user.avatar_key,
            timezone=user.timezone,
            createdAt=user.created_at,
        )

    async def get_stats(self) -> AdminStatsResponse:
        clients = await self.users.count_by_role("client")
        coaches = await self.users.count_by_role("coach")
        admins = await self.users.count_by_role("admin")
        recent = await self.users.recent_users(5)
        return AdminStatsResponse(
            clients=clients,
            coaches=coaches,
            admins=admins,
            recentUsers=[self._to_public_with_created(u) for u in recent],
        )

    async def list_users(
        self, role: str | None, search: str | None, page: int, page_size: int
    ) -> AdminUserListResponse:
        users, total = await self.users.list_users(role, search, page, page_size)
        return AdminUserListResponse(
            items=[self._to_public_with_created(u) for u in users],
            page=page,
            pageSize=page_size,
            total=total,
            hasNextPage=page * page_size < total,
        )

    async def create_coach(self, data: CreateCoachRequest) -> UserPublicWithCreated:
        if await self.users.username_exists(data.username):
            raise ConflictError("Username already exists")
        user = User(
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            password_hash=hash_password(data.password),
            role="coach",
        )
        await self.users.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return self._to_public_with_created(user)

    async def elevate_to_coach(self, user_id: UUID) -> UserPublicWithCreated:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.role != "client":
            raise ValidationError("Only clients can be elevated to coach")
        user.role = "coach"
        await self.audit_logs.log("elevate_to_coach", target_user_id=user.id)
        await self.db.commit()
        await self.db.refresh(user)
        return self._to_public_with_created(user)

    async def delete_user(self, admin_id: UUID, user_id: UUID, data: AdminDeleteUserRequest) -> None:
        admin = await self.users.get_by_id(admin_id)
        target = await self.users.get_by_id(user_id)
        if not admin or not target:
            raise NotFoundError("User not found")
        if admin.id == target.id:
            raise ForbiddenError("Cannot delete your own account through admin endpoint")
        if not verify_password(data.admin_password, admin.password_hash):
            raise UnauthorizedError("Admin password is incorrect")
        if data.confirm_username.lower() != target.username.lower():
            raise ValidationError("Username confirmation does not match")
        if target.role == "admin":
            admin_count = await self.users.count_by_role("admin")
            if admin_count <= 1:
                raise ValidationError("Cannot delete the last admin account")
        await self.audit_logs.log(
            "admin_delete_user",
            actor_user_id=admin.id,
            target_user_id=target.id,
            metadata={"username": target.username},
        )
        await self.users.delete(target)
        await self.db.commit()
