import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assigned_task import AssignedTask
from app.db.models.coach_client import CoachClient
from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_checklist_completion_persists(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "taskcoach", "coach")
    client_user = await create_user(db_session, "taskclient", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    task = AssignedTask(
        coach_id=coach.id,
        client_id=client_user.id,
        title="Drink water",
        active_from=date(2026, 7, 4),
    )
    db_session.add(task)
    await db_session.commit()
    token = await login(client, "taskclient")
    response = await client.patch(
        f"/api/me/checklist/{task.id}/completion",
        headers={"Authorization": f"Bearer {token}"},
        json={"date": "2026-07-04", "completed": True},
    )
    assert response.status_code == 204
    checklist = await client.get(
        "/api/me/checklist?date=2026-07-04",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert checklist.json()["tasks"][0]["completed"] is True


@pytest.mark.asyncio
async def test_checklist_respects_daily_interval(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "intervalcoach", "coach")
    client_user = await create_user(db_session, "intervalclient", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    task = AssignedTask(
        coach_id=coach.id,
        client_id=client_user.id,
        title="Rest day walk",
        active_from=date(2026, 7, 1),
        recurrence_frequency="daily",
        recurrence_interval=2,
        recurrence_days=[],
    )
    db_session.add(task)
    await db_session.commit()

    token = await login(client, "intervalclient")
    day_one = await client.get(
        "/api/me/checklist?date=2026-07-01",
        headers={"Authorization": f"Bearer {token}"},
    )
    day_two = await client.get(
        "/api/me/checklist?date=2026-07-02",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(day_one.json()["tasks"]) == 1
    assert len(day_two.json()["tasks"]) == 0


@pytest.mark.asyncio
async def test_daily_notes_visible_to_coach(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "notecoach", "coach")
    client_user = await create_user(db_session, "noteclient", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    client_token = await login(client, "noteclient")
    await client.put(
        "/api/me/daily-note",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"date": "2026-07-04", "body": "Felt great today."},
    )
    coach_token = await login(client, "notecoach")
    response = await client.get(
        f"/api/coach/clients/{client_user.id}/daily-notes?startDate=2026-07-04&endDate=2026-07-04",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["body"] == "Felt great today."
