"""Create initial admin user if one does not exist."""

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import AsyncSessionLocal

settings = get_settings()


async def create_initial_admin() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role == "admin", User.username == settings.INITIAL_ADMIN_USERNAME)
        )
        if result.scalar_one_or_none():
            print("Initial admin already exists.")
            return
        admin = User(
            username=settings.INITIAL_ADMIN_USERNAME,
            first_name=settings.INITIAL_ADMIN_FIRST_NAME,
            last_name=settings.INITIAL_ADMIN_LAST_NAME,
            password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
            role="admin",
        )
        session.add(admin)
        await session.commit()
        print(f"Initial admin created: {settings.INITIAL_ADMIN_USERNAME}")


if __name__ == "__main__":
    asyncio.run(create_initial_admin())
