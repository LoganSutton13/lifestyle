import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_measurement_saves_normalized_base(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "measureclient", "client")
    await db_session.commit()
    token = await login(client, "measureclient")
    response = await client.post(
        "/api/me/measurements",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "typeKey": "body_weight",
            "value": 200,
            "unitKey": "lb",
            "recordedAt": "2026-07-04T15:45:00Z",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_measurement_rejects_long_range(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "rangeclient", "client")
    await db_session.commit()
    token = await login(client, "rangeclient")
    response = await client.get(
        "/api/me/measurements?typeKey=body_weight&startDate=2020-01-01&endDate=2026-07-04&unitKey=lb",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_measurement_range_uses_user_timezone(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "tzclient", "client", timezone="America/Los_Angeles")
    await db_session.commit()
    token = await login(client, "tzclient")

    create_response = await client.post(
        "/api/me/measurements",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "typeKey": "body_weight",
            "value": 180,
            "unitKey": "lb",
            "recordedAt": "2026-07-06T05:00:00Z",
        },
    )
    assert create_response.status_code == 201

    graph_response = await client.get(
        "/api/me/measurements?typeKey=body_weight&startDate=2026-07-05&endDate=2026-07-05&unitKey=lb",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert graph_response.status_code == 200
    points = graph_response.json()["points"]
    assert len(points) == 1
    assert points[0]["value"] == "180.0"


@pytest.mark.asyncio
async def test_profile_update_rejects_invalid_timezone(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "profileclient", "client")
    await db_session.commit()
    token = await login(client, "profileclient")
    response = await client.put(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"timezone": "Not/A/Timezone"},
    )
    assert response.status_code == 422
