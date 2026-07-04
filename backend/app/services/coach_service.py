from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.db.models.coach_client import CoachClient
from app.db.models.user import User
from app.repositories.checklist import ChecklistRepository
from app.repositories.coach_clients import CoachClientRepository
from app.repositories.measurements import MeasurementRepository
from app.repositories.users import UserRepository
from app.schemas.coach import (
    AddClientRequest,
    ClientSearchResponse,
    ClientSearchResult,
    CoachClientListResponse,
    CoachClientSummary,
)
from app.services.unit_conversion import from_base_value


class CoachService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.coach_clients = CoachClientRepository(db)
        self.measurements = MeasurementRepository(db)
        self.checklist = ChecklistRepository(db)

    async def assert_coach_has_client(self, coach_id: UUID, client_id: UUID) -> None:
        if not await self.coach_clients.exists(coach_id, client_id):
            raise ForbiddenError("Client is not associated with this coach")

    async def list_clients(
        self, coach_id: UUID, search: str | None, page: int, page_size: int
    ) -> CoachClientListResponse:
        query = (
            select(User, CoachClient)
            .join(CoachClient, CoachClient.client_id == User.id)
            .where(CoachClient.coach_id == coach_id)
        )
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(User.username).like(pattern)
                | func.lower(User.first_name).like(pattern)
                | func.lower(User.last_name).like(pattern)
            )
        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        query = query.order_by(CoachClient.assigned_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        rows = result.all()
        items: list[CoachClientSummary] = []
        today = date.today()
        for user, _assoc in rows:
            latest = await self.measurements.latest_body_weight(user.id)
            latest_weight = None
            if latest:
                unit = await self.measurements.get_unit("lb")
                if unit:
                    latest_weight = from_base_value(latest.value_base, unit).quantize(Decimal("0.1"))
            completed, total_tasks = await self.checklist.count_today_completion(user.id, today)
            items.append(
                CoachClientSummary(
                    id=user.id,
                    username=user.username,
                    firstName=user.first_name,
                    lastName=user.last_name,
                    avatarKey=user.avatar_key,
                    latestBodyWeight=latest_weight,
                    todayCompletedTasks=completed,
                    todayTotalTasks=total_tasks,
                )
            )
        return CoachClientListResponse(
            items=items,
            page=page,
            pageSize=page_size,
            total=total,
            hasNextPage=page * page_size < total,
        )

    async def search_clients(self, coach_id: UUID, query_str: str) -> ClientSearchResponse:
        pattern = f"%{query_str.lower()}%"
        result = await self.db.execute(
            select(User)
            .where(
                User.role == "client",
                func.lower(User.username).like(pattern)
                | func.lower(User.first_name).like(pattern)
                | func.lower(User.last_name).like(pattern),
            )
            .limit(20)
        )
        clients = list(result.scalars().all())
        items = []
        for user in clients:
            if await self.coach_clients.exists(coach_id, user.id):
                continue
            items.append(
                ClientSearchResult(
                    id=user.id,
                    username=user.username,
                    firstName=user.first_name,
                    lastName=user.last_name,
                    avatarKey=user.avatar_key,
                )
            )
        return ClientSearchResponse(items=items)

    async def add_client(self, coach_id: UUID, data: AddClientRequest) -> None:
        client = await self.users.get_by_id(data.client_id)
        if not client or client.role != "client":
            raise NotFoundError("Client not found")
        if await self.coach_clients.exists(coach_id, data.client_id):
            raise ConflictError("Client is already associated with this coach")
        await self.coach_clients.add(coach_id, data.client_id)
        await self.db.commit()

    async def remove_client(self, coach_id: UUID, client_id: UUID) -> None:
        removed = await self.coach_clients.remove(coach_id, client_id)
        if not removed:
            raise NotFoundError("Client association not found")
        await self.db.commit()
