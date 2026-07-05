from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import NotFoundError, ValidationError
from app.db.models.meal import Meal
from app.db.models.meal_assignment import MealAssignment
from app.repositories.meals import MealRepository
from app.schemas.meals import MealCreateRequest, MealItem, MealListResponse, MealUpdateRequest


class MealService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.meals = MealRepository(db)

    def _to_item(self, meal: Meal, assignment: MealAssignment, category) -> MealItem:
        return MealItem(
            id=meal.id,
            name=meal.name,
            category=meal.category_key,
            categoryLabel=category.display_name,
            description=meal.description,
            assignedAt=assignment.assigned_at,
        )

    async def list_client_meals(
        self, client_id: UUID, category: str | None, page: int, page_size: int
    ) -> MealListResponse:
        page_size = min(page_size, 50)
        if category:
            cat = await self.meals.get_category(category)
            if not cat:
                raise ValidationError("Invalid meal category")
        rows, total = await self.meals.list_for_client(client_id, category, page, page_size)
        return MealListResponse(
            items=[self._to_item(m, a, c) for m, a, c in rows],
            page=page,
            pageSize=page_size,
            total=total,
            hasNextPage=page * page_size < total,
        )

    async def list_coach_client_meals(
        self, coach_id: UUID, client_id: UUID, category: str | None, page: int, page_size: int
    ) -> MealListResponse:
        if category:
            cat = await self.meals.get_category(category)
            if not cat:
                raise ValidationError("Invalid meal category")
        rows, total = await self.meals.list_for_coach_client(coach_id, client_id, category, page, page_size)
        return MealListResponse(
            items=[self._to_item(m, a, c) for m, a, c in rows],
            page=page,
            pageSize=page_size,
            total=total,
            hasNextPage=page * page_size < total,
        )

    async def create_meal_for_client(
        self, coach_id: UUID, client_id: UUID, data: MealCreateRequest
    ) -> MealItem:
        category = await self.meals.get_category(data.category)
        if not category:
            raise ValidationError("Invalid meal category")
        meal = Meal(
            coach_id=coach_id,
            name=data.name,
            category_key=data.category,
            description=data.description,
        )
        await self.meals.add(meal)
        assignment = MealAssignment(
            meal_id=meal.id,
            client_id=client_id,
            assigned_by_coach_id=coach_id,
        )
        await self.meals.add_assignment(assignment)
        await self.db.commit()
        await self.db.refresh(meal)
        return self._to_item(meal, assignment, category)

    async def update_meal(
        self, coach_id: UUID, client_id: UUID, meal_id: UUID, data: MealUpdateRequest
    ) -> MealItem:
        meal = await self.meals.get_by_id(meal_id)
        if not meal or meal.coach_id != coach_id:
            raise NotFoundError("Meal not found")
        if data.name is not None:
            meal.name = data.name
        if data.category is not None:
            category = await self.meals.get_category(data.category)
            if not category:
                raise ValidationError("Invalid meal category")
            meal.category_key = data.category
        else:
            category = await self.meals.get_category(meal.category_key)
        if data.description is not None:
            meal.description = data.description
        assignment = await self.meals.get_assignment(meal_id, client_id)
        if not assignment:
            raise NotFoundError("Meal assignment not found")
        await self.db.commit()
        await self.db.refresh(meal)
        return self._to_item(meal, assignment, category)

    async def delete_meal(self, coach_id: UUID, meal_id: UUID) -> None:
        meal = await self.meals.get_by_id(meal_id)
        if not meal or meal.coach_id != coach_id:
            raise NotFoundError("Meal not found")
        await self.meals.delete(meal)
        await self.db.commit()
