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
            "repeatsDaily": True,
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
            "repeatsDaily": False,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "12k steps"
    assert updated["description"] == "Walk more today"
    assert updated["activeFrom"] == "2026-07-02"
    assert updated["activeUntil"] == "2026-07-31"
    assert updated["repeatsDaily"] is False

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
