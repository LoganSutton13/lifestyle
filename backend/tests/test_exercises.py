import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_client_can_list_active_exercises(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "execlient1", "client")
    await db_session.commit()
    token = await login(client, "execlient1")

    response = await client.get(
        "/api/exercises", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    assert all(item["archivedAt"] is None for item in data["items"])


@pytest.mark.asyncio
async def test_client_cannot_create_exercise(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "execlient2", "client")
    await db_session.commit()
    token = await login(client, "execlient2")

    response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Client Made Exercise",
            "equipmentKey": "barbell",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["chest"],
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_coach_can_create_global_exercise(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "execoach1", "coach")
    await db_session.commit()
    token = await login(client, "execoach1")

    response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Incline Dumbbell Press",
            "equipmentKey": "dumbbell",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["chest"],
            "secondaryMuscleKeys": ["triceps", "shoulders"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Incline Dumbbell Press"
    assert data["equipment"]["key"] == "dumbbell"
    assert data["primaryMuscles"][0]["key"] == "chest"


@pytest.mark.asyncio
async def test_admin_can_create_global_exercise(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "exeadmin1", "admin")
    await db_session.commit()
    token = await login(client, "exeadmin1")

    response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Cable Fly",
            "equipmentKey": "cable",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["chest"],
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_duplicate_exercise_returns_409(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "execoach2", "coach")
    await db_session.commit()
    token = await login(client, "execoach2")

    payload = {
        "name": "Front Squat",
        "equipmentKey": "barbell",
        "trackingType": "reps_load",
        "primaryMuscleKeys": ["quadriceps"],
    }
    first = await client.post(
        "/api/exercises", headers={"Authorization": f"Bearer {token}"}, json=payload
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={**payload, "name": "front squat"},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_EXERCISE"


@pytest.mark.asyncio
async def test_archived_exercise_hidden_from_client_search(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "execoach3", "coach")
    await create_user(db_session, "execlient3", "client")
    await db_session.commit()
    coach_token = await login(client, "execoach3")

    create_response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "name": "Zercher Squat",
            "equipmentKey": "barbell",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["quadriceps"],
        },
    )
    exercise_id = create_response.json()["id"]

    archive_response = await client.delete(
        f"/api/exercises/{exercise_id}", headers={"Authorization": f"Bearer {coach_token}"}
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["archivedAt"] is not None

    client_token = await login(client, "execlient3")
    search_response = await client.get(
        "/api/exercises?query=zercher", headers={"Authorization": f"Bearer {client_token}"}
    )
    assert search_response.status_code == 200
    assert search_response.json()["items"] == []


@pytest.mark.asyncio
async def test_coach_cannot_edit_another_coachs_exercise(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "execoach4", "coach")
    await create_user(db_session, "execoach5", "coach")
    await db_session.commit()
    coach1_token = await login(client, "execoach4")
    coach2_token = await login(client, "execoach5")

    create_response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {coach1_token}"},
        json={
            "name": "Trap Bar Deadlift",
            "equipmentKey": "barbell",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["back"],
        },
    )
    exercise_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/exercises/{exercise_id}",
        headers={"Authorization": f"Bearer {coach2_token}"},
        json={"instructions": "Hacked"},
    )
    assert update_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_edit_or_archive_any_exercise(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "execoach6", "coach")
    await create_user(db_session, "exeadmin2", "admin")
    await db_session.commit()
    coach_token = await login(client, "execoach6")
    admin_token = await login(client, "exeadmin2")

    create_response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "name": "Sumo Deadlift",
            "equipmentKey": "barbell",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["glutes"],
        },
    )
    exercise_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/exercises/{exercise_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"instructions": "Keep your back flat."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["instructions"] == "Keep your back flat."

    archive_response = await client.delete(
        f"/api/exercises/{exercise_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["archivedAt"] is not None


@pytest.mark.asyncio
async def test_referenced_exercise_tracking_type_cannot_be_changed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "execoach7", "coach")
    client_user = await create_user(db_session, "execlient4", "client")
    await db_session.commit()
    coach_token = await login(client, "execoach7")
    client_token = await login(client, "execlient4")

    create_response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "name": "Hack Squat",
            "equipmentKey": "machine",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["quadriceps"],
        },
    )
    exercise_id = create_response.json()["id"]

    start_response = await client.post(
        "/api/me/workouts",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"mode": "freestyle"},
    )
    session_id = start_response.json()["id"]
    await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"exerciseId": exercise_id},
    )

    update_response = await client.patch(
        f"/api/exercises/{exercise_id}",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"trackingType": "reps_only"},
    )
    assert update_response.status_code == 400


@pytest.mark.asyncio
async def test_exercise_creation_writes_audit_log(client: AsyncClient, db_session: AsyncSession) -> None:
    coach = await create_user(db_session, "execoach8", "coach")
    await db_session.commit()
    token = await login(client, "execoach8")

    response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Goblet Squat",
            "equipmentKey": "dumbbell",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["quadriceps"],
        },
    )
    assert response.status_code == 201

    audit_result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "exercise.created", AuditLog.actor_user_id == coach.id)
    )
    entries = audit_result.scalars().all()
    assert len(entries) == 1


@pytest.mark.asyncio
async def test_restore_is_admin_only(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "execoach9", "coach")
    await create_user(db_session, "exeadmin3", "admin")
    await db_session.commit()
    coach_token = await login(client, "execoach9")
    admin_token = await login(client, "exeadmin3")

    create_response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "name": "Reverse Lunge",
            "equipmentKey": "bodyweight",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["quadriceps"],
        },
    )
    exercise_id = create_response.json()["id"]
    await client.delete(f"/api/exercises/{exercise_id}", headers={"Authorization": f"Bearer {coach_token}"})

    coach_restore = await client.post(
        f"/api/exercises/{exercise_id}/restore", headers={"Authorization": f"Bearer {coach_token}"}
    )
    assert coach_restore.status_code == 403

    admin_restore = await client.post(
        f"/api/exercises/{exercise_id}/restore", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_restore.status_code == 200
    assert admin_restore.json()["archivedAt"] is None
