from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(func.lower(User.username) == username.lower()))
        return result.scalar_one_or_none()

    async def username_exists(self, username: str, exclude_id: UUID | None = None) -> bool:
        query = select(User.id).where(func.lower(User.username) == username.lower())
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def count_by_role(self, role: str) -> int:
        result = await self.db.execute(select(func.count()).select_from(User).where(User.role == role))
        return result.scalar_one()

    async def list_users(
        self, role: str | None = None, search: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        query = select(User)
        if role:
            query = query.where(User.role == role)
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(User.username).like(pattern)
                | func.lower(User.first_name).like(pattern)
                | func.lower(User.last_name).like(pattern)
            )
        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def recent_users(self, limit: int = 5) -> list[User]:
        result = await self.db.execute(select(User).order_by(User.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def add(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
