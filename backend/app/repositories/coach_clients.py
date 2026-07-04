from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.coach_client import CoachClient


class CoachClientRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def exists(self, coach_id: UUID, client_id: UUID) -> bool:
        result = await self.db.execute(
            select(CoachClient).where(CoachClient.coach_id == coach_id, CoachClient.client_id == client_id)
        )
        return result.scalar_one_or_none() is not None

    async def add(self, coach_id: UUID, client_id: UUID) -> CoachClient:
        association = CoachClient(coach_id=coach_id, client_id=client_id)
        self.db.add(association)
        await self.db.flush()
        return association

    async def remove(self, coach_id: UUID, client_id: UUID) -> bool:
        result = await self.db.execute(
            select(CoachClient).where(CoachClient.coach_id == coach_id, CoachClient.client_id == client_id)
        )
        association = result.scalar_one_or_none()
        if not association:
            return False
        await self.db.delete(association)
        return True
