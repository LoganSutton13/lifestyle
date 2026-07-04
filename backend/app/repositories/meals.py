from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.meal import Meal
from app.db.models.meal_assignment import MealAssignment
from app.db.models.meal_category import MealCategory


class MealRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, meal_id: UUID) -> Meal | None:
        result = await self.db.execute(select(Meal).where(Meal.id == meal_id))
        return result.scalar_one_or_none()

    async def list_for_client(
        self, client_id: UUID, category: str | None = None, page: int = 1, page_size: int = 10
    ) -> tuple[list[tuple[Meal, MealAssignment, MealCategory]], int]:
        query = (
            select(Meal, MealAssignment, MealCategory)
            .join(MealAssignment, MealAssignment.meal_id == Meal.id)
            .join(MealCategory, MealCategory.key == Meal.category_key)
            .where(MealAssignment.client_id == client_id, MealCategory.active.is_(True))
        )
        if category:
            query = query.where(Meal.category_key == category)
        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        query = query.order_by(MealAssignment.assigned_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.all()), total

    async def list_for_coach_client(
        self, coach_id: UUID, client_id: UUID, category: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[tuple[Meal, MealAssignment, MealCategory]], int]:
        query = (
            select(Meal, MealAssignment, MealCategory)
            .join(MealAssignment, MealAssignment.meal_id == Meal.id)
            .join(MealCategory, MealCategory.key == Meal.category_key)
            .where(
                Meal.coach_id == coach_id,
                MealAssignment.client_id == client_id,
            )
        )
        if category:
            query = query.where(Meal.category_key == category)
        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        query = query.order_by(MealAssignment.assigned_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.all()), total

    async def add(self, meal: Meal) -> Meal:
        self.db.add(meal)
        await self.db.flush()
        return meal

    async def add_assignment(self, assignment: MealAssignment) -> MealAssignment:
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def delete(self, meal: Meal) -> None:
        await self.db.delete(meal)

    async def get_category(self, key: str) -> MealCategory | None:
        result = await self.db.execute(
            select(MealCategory).where(MealCategory.key == key, MealCategory.active.is_(True))
        )
        return result.scalar_one_or_none()
