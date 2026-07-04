import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.coach_client import CoachClient
from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_client_cannot_access_other_client_meals(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    client_a = await create_user(db_session, "clienta", "client")
    await create_user(db_session, "clientb", "client")
    await db_session.commit()
    token = await login(client, "clienta")
    response = await client.get(
        "/api/me/meals",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_coach_cannot_access_unassociated_client(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "coach1", "coach")
    client_user = await create_user(db_session, "client1", "client")
    await db_session.commit()
    token = await login(client, "coach1")
    response = await client.get(
        f"/api/coach/clients/{client_user.id}/meals",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_coach_can_access_associated_client(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "coach2", "coach")
    client_user = await create_user(db_session, "client2", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    token = await login(client, "coach2")
    response = await client.get(
        f"/api/coach/clients/{client_user.id}/meals",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
