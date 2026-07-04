import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_admin_create_coach(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "superadmin", "admin")
    await db_session.commit()
    token = await login(client, "superadmin")
    response = await client.post(
        "/api/admin/coaches",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "newcoach",
            "firstName": "New",
            "lastName": "Coach",
            "password": "SecurePass123!",
            "passwordConfirm": "SecurePass123!",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "coach"


@pytest.mark.asyncio
async def test_elevate_client_to_coach(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "admin2", "admin")
    client_user = await create_user(db_session, "elevateme", "client")
    await db_session.commit()
    token = await login(client, "admin2")
    response = await client.patch(
        f"/api/admin/users/{client_user.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "coach"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "coach"


@pytest.mark.asyncio
async def test_cannot_delete_last_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_user(db_session, "onlyadmin", "admin")
    await db_session.commit()
    token = await login(client, "onlyadmin")
    response = await client.request(
        "DELETE",
        f"/api/admin/users/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"adminPassword": "SecurePass123!", "confirmUsername": "onlyadmin"},
    )
    assert response.status_code == 403
