import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.coach_client import CoachClient
from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_coach_can_update_client_task(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "updcoach", "coach")
    client_user = await create_user(db_session, "updclient", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    token = await login(client, "updcoach")

    create_response = await client.post(
        f"/api/coach/clients/{client_user.id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "10k steps",
            "description": "Walk today",
            "activeFrom": "2026-07-01",
            "recurrenceFrequency": "daily",
            "recurrenceInterval": 1,
            "recurrenceDays": [],
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/coach/clients/{client_user.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "12k steps",
            "description": "Walk more today",
            "activeFrom": "2026-07-02",
            "activeUntil": "2026-07-31",
            "recurrenceFrequency": "weekly",
            "recurrenceInterval": 2,
            "recurrenceDays": [2],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "12k steps"
    assert updated["description"] == "Walk more today"
    assert updated["activeFrom"] == "2026-07-02"
    assert updated["activeUntil"] == "2026-07-31"
    assert updated["recurrenceFrequency"] == "weekly"
    assert updated["recurrenceInterval"] == 2
    assert updated["recurrenceDays"] == [2]

    list_response = await client.get(
        f"/api/coach/clients/{client_user.id}/tasks?active=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "12k steps"


@pytest.mark.asyncio
async def test_coach_cannot_update_task_for_unassociated_client(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "taskcoach403", "coach")
    other_coach = await create_user(db_session, "othcoach", "coach")
    client_user = await create_user(db_session, "taskclient403", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()

    coach_token = await login(client, "taskcoach403")
    create_response = await client.post(
        f"/api/coach/clients/{client_user.id}/tasks",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"title": "Drink water", "activeFrom": "2026-07-01"},
    )
    task_id = create_response.json()["id"]

    other_token = await login(client, "othcoach")
    response = await client.patch(
        f"/api/coach/clients/{client_user.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"title": "Hacked"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_coach_update_task_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "taskcoach404", "coach")
    client_user = await create_user(db_session, "taskclient404", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    token = await login(client, "taskcoach404")

    response = await client.patch(
        f"/api/coach/clients/{client_user.id}/tasks/00000000-0000-0000-0000-000000000001",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Missing"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_weekly_task_appears_only_on_selected_weekday(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "weekcoach", "coach")
    client_user = await create_user(db_session, "weekclient", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()

    coach_token = await login(client, "weekcoach")
    create_response = await client.post(
        f"/api/coach/clients/{client_user.id}/tasks",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "title": "Leg day",
            "activeFrom": "2026-07-01",
            "recurrenceFrequency": "weekly",
            "recurrenceInterval": 1,
            "recurrenceDays": [2],
        },
    )
    assert create_response.status_code == 201

    client_token = await login(client, "weekclient")
    wednesday = await client.get(
        "/api/me/checklist?date=2026-07-01",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert wednesday.status_code == 200
    assert len(wednesday.json()["tasks"]) == 1

    thursday = await client.get(
        "/api/me/checklist?date=2026-07-02",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert thursday.status_code == 200
    assert len(thursday.json()["tasks"]) == 0


@pytest.mark.asyncio
async def test_biweekly_task_alternates_weeks(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "biweekcoach", "coach")
    client_user = await create_user(db_session, "biweekclient", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()

    coach_token = await login(client, "biweekcoach")
    await client.post(
        f"/api/coach/clients/{client_user.id}/tasks",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "title": "Long run",
            "activeFrom": "2026-07-01",
            "recurrenceFrequency": "weekly",
            "recurrenceInterval": 2,
            "recurrenceDays": [2],
        },
    )

    client_token = await login(client, "biweekclient")
    week_one = await client.get(
        "/api/me/checklist?date=2026-07-01",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    week_two = await client.get(
        "/api/me/checklist?date=2026-07-08",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    week_three = await client.get(
        "/api/me/checklist?date=2026-07-15",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert len(week_one.json()["tasks"]) == 1
    assert len(week_two.json()["tasks"]) == 0
    assert len(week_three.json()["tasks"]) == 1
