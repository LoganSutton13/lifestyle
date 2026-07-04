import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_register_creates_client(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "samfit",
            "firstName": "Sam",
            "lastName": "Rivera",
            "password": "SecurePass123!",
            "passwordConfirm": "SecurePass123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["role"] == "client"
    assert "accessToken" in data


@pytest.mark.asyncio
async def test_duplicate_username_case_insensitive(client: AsyncClient) -> None:
    payload = {
        "username": "TestUser",
        "firstName": "A",
        "lastName": "B",
        "password": "SecurePass123!",
        "passwordConfirm": "SecurePass123!",
    }
    assert (await client.post("/api/auth/register", json=payload)).status_code == 201
    payload["username"] = "testuser"
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "loginuser", "client")
    await db_session.commit()
    response = await client.post(
        "/api/auth/login",
        json={"username": "loginuser", "password": "SecurePass123!"},
    )
    assert response.status_code == 200
    assert "accessToken" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "badpass", "client")
    await db_session.commit()
    response = await client.post(
        "/api/auth/login",
        json={"username": "badpass", "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_without_token(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
