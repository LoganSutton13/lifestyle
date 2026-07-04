import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.coach_client import CoachClient
from app.db.models.meal import Meal
from app.db.models.meal_assignment import MealAssignment
from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_meal_pagination_default_10(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "mealcoach", "coach")
    client_user = await create_user(db_session, "mealclient", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    for i in range(12):
        meal = Meal(coach_id=coach.id, name=f"Meal {i}", category_key="breakfast")
        db_session.add(meal)
        await db_session.flush()
        db_session.add(
            MealAssignment(
                meal_id=meal.id,
                client_id=client_user.id,
                assigned_by_coach_id=coach.id,
            )
        )
    await db_session.commit()
    token = await login(client, "mealclient")
    response = await client.get(
        "/api/me/meals",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pageSize"] == 10
    assert len(data["items"]) == 10
    assert data["hasNextPage"] is True


@pytest.mark.asyncio
async def test_meal_category_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "filtercoach", "coach")
    client_user = await create_user(db_session, "filterclient", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    breakfast = Meal(coach_id=coach.id, name="Eggs", category_key="breakfast")
    lunch = Meal(coach_id=coach.id, name="Salad", category_key="lunch")
    db_session.add_all([breakfast, lunch])
    await db_session.flush()
    for meal in [breakfast, lunch]:
        db_session.add(
            MealAssignment(
                meal_id=meal.id,
                client_id=client_user.id,
                assigned_by_coach_id=coach.id,
            )
        )
    await db_session.commit()
    token = await login(client, "filterclient")
    response = await client.get(
        "/api/me/meals?category=breakfast",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["category"] == "breakfast"
