import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.exercise import Exercise
from tests.conftest import create_user, login


async def _get_exercise_id(db_session: AsyncSession, slug: str) -> str:
    result = await db_session.execute(select(Exercise).where(Exercise.slug == slug))
    exercise = result.scalar_one()
    return str(exercise.id)


@pytest.mark.asyncio
async def test_client_can_start_freestyle_workout(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "wclient1", "client")
    await db_session.commit()
    token = await login(client, "wclient1")

    response = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "freestyle"
    assert data["status"] == "in_progress"
    assert data["exercises"] == []

    active_response = await client.get(
        "/api/me/workouts/active", headers={"Authorization": f"Bearer {token}"}
    )
    assert active_response.status_code == 200
    assert active_response.json()["session"]["id"] == data["id"]


@pytest.mark.asyncio
async def test_starting_second_freestyle_returns_conflict(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient2", "client")
    await db_session.commit()
    token = await login(client, "wclient2")

    first = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    assert second.status_code == 409
    body = second.json()
    assert body["error"]["code"] == "ACTIVE_WORKOUT_EXISTS"
    assert body["error"]["details"]["sessionId"] == first.json()["id"]


@pytest.mark.asyncio
async def test_client_cannot_read_or_mutate_another_clients_session(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient3", "client")
    await create_user(db_session, "wclient4", "client")
    await db_session.commit()
    token1 = await login(client, "wclient3")
    token2 = await login(client, "wclient4")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token1}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]

    read_response = await client.get(
        f"/api/me/workouts/{session_id}", headers={"Authorization": f"Bearer {token2}"}
    )
    assert read_response.status_code == 404

    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    mutate_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token2}"},
        json={"exerciseId": exercise_id},
    )
    assert mutate_response.status_code == 404


@pytest.mark.asyncio
async def test_add_exercise_and_add_set(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "wclient5", "client")
    await db_session.commit()
    token = await login(client, "wclient5")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")

    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    assert add_exercise_response.status_code == 201
    session_exercise = add_exercise_response.json()
    assert session_exercise["position"] == 0
    assert session_exercise["exercise"]["trackingType"] == "reps_load"

    add_set_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise['id']}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "reps": 10, "loadValue": "45", "loadUnitKey": "lb"},
    )
    assert add_set_response.status_code == 201
    set_data = add_set_response.json()
    assert set_data["loadValue"] == "45.0000"
    assert set_data["loadUnitKey"] == "lb"
    assert set_data["completedAt"] is None


@pytest.mark.asyncio
async def test_cannot_add_archived_exercise(client: AsyncClient, db_session: AsyncSession) -> None:
    coach = await create_user(db_session, "wcoach1", "coach")
    await create_user(db_session, "wclient6", "client")
    await db_session.commit()
    coach_token = await login(client, "wcoach1")
    client_token = await login(client, "wclient6")

    create_response = await client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "name": "Archived Curl",
            "equipmentKey": "dumbbell",
            "trackingType": "reps_load",
            "primaryMuscleKeys": ["biceps"],
        },
    )
    exercise_id = create_response.json()["id"]
    await client.delete(f"/api/exercises/{exercise_id}", headers={"Authorization": f"Bearer {coach_token}"})

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {client_token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]

    response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"exerciseId": exercise_id},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EXERCISE_ARCHIVED"


@pytest.mark.asyncio
async def test_removing_exercise_deletes_its_sets(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "wclient7", "client")
    await db_session.commit()
    token = await login(client, "wclient7")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-back-squat")

    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]
    await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "reps": 5},
    )

    remove_response = await client.delete(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert remove_response.status_code == 204

    detail_response = await client.get(
        f"/api/me/workouts/{session_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert detail_response.json()["exercises"] == []


@pytest.mark.asyncio
async def test_reorder_rejects_invalid_arrays(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "wclient8", "client")
    await db_session.commit()
    token = await login(client, "wclient8")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    ex1 = await _get_exercise_id(db_session, "barbell-bench-press")
    ex2 = await _get_exercise_id(db_session, "barbell-back-squat")

    r1 = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": ex1},
    )
    r2 = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": ex2},
    )
    se1 = r1.json()["id"]
    se2 = r2.json()["id"]

    missing_response = await client.put(
        f"/api/me/workouts/{session_id}/exercise-order",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseIds": [se1]},
    )
    assert missing_response.status_code == 400

    duplicate_response = await client.put(
        f"/api/me/workouts/{session_id}/exercise-order",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseIds": [se1, se1]},
    )
    assert duplicate_response.status_code == 400

    valid_response = await client.put(
        f"/api/me/workouts/{session_id}/exercise-order",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseIds": [se2, se1]},
    )
    assert valid_response.status_code == 200
    reordered = valid_response.json()
    assert reordered[0]["id"] == se2
    assert reordered[0]["position"] == 0
    assert reordered[1]["id"] == se1
    assert reordered[1]["position"] == 1


@pytest.mark.asyncio
async def test_update_load_stores_input_unit_and_normalized_kg(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient9", "client")
    await db_session.commit()
    token = await login(client, "wclient9")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]
    add_set_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal"},
    )
    set_id = add_set_response.json()["id"]

    update_response = await client.patch(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets/{set_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"reps": 8, "loadValue": "100", "loadUnitKey": "lb"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["loadValue"] == "100.0000"
    assert updated["loadUnitKey"] == "lb"

    from uuid import UUID

    from app.db.models.workout_session import WorkoutSet

    row = await db_session.get(WorkoutSet, UUID(set_id))
    assert row is not None
    assert abs(float(row.load_value_base) - 45.359237) < 0.001


@pytest.mark.asyncio
async def test_invalid_negative_load_is_rejected(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "wclient10", "client")
    await db_session.commit()
    token = await login(client, "wclient10")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]

    response = await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "loadValue": "-5", "loadUnitKey": "lb"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reps_only_exercise_rejects_completed_set_without_reps(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient11", "client")
    await db_session.commit()
    token = await login(client, "wclient11")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "pull-up")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]
    add_set_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal"},
    )
    set_id = add_set_response.json()["id"]

    response = await client.patch(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets/{set_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"completed": True},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_SET_METRICS"


@pytest.mark.asyncio
async def test_duration_exercise_rejects_completed_set_without_duration(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient12", "client")
    await db_session.commit()
    token = await login(client, "wclient12")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "plank")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]
    add_set_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal"},
    )
    set_id = add_set_response.json()["id"]

    response = await client.patch(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets/{set_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"completed": True},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_SET_METRICS"


@pytest.mark.asyncio
async def test_set_cannot_be_accessed_through_another_sessions_path(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient13", "client")
    await db_session.commit()
    token = await login(client, "wclient13")

    start1 = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session1_id = start1.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session1_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]
    add_set_response = await client.post(
        f"/api/me/workouts/{session1_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "reps": 5},
    )
    set_id = add_set_response.json()["id"]

    # Discard session 1, start a fresh session, then try to reach the old set via the new session id.
    await client.delete(
        f"/api/me/workouts/{session1_id}", headers={"Authorization": f"Bearer {token}"}
    )
    start2 = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session2_id = start2.json()["id"]

    response = await client.patch(
        f"/api/me/workouts/{session2_id}/exercises/{session_exercise_id}/sets/{set_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"reps": 1},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deleting_set_renumbers_positions(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "wclient14", "client")
    await db_session.commit()
    token = await login(client, "wclient14")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]

    set_ids = []
    for _ in range(3):
        r = await client.post(
            f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
            headers={"Authorization": f"Bearer {token}"},
            json={"setType": "normal", "reps": 5},
        )
        set_ids.append(r.json()["id"])

    delete_response = await client.delete(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets/{set_ids[0]}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    detail = await client.get(
        f"/api/me/workouts/{session_id}", headers={"Authorization": f"Bearer {token}"}
    )
    sets = detail.json()["exercises"][0]["sets"]
    positions = sorted(s["position"] for s in sets)
    assert positions == [0, 1]


@pytest.mark.asyncio
async def test_drop_set_type_persists(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "wclient15", "client")
    await db_session.commit()
    token = await login(client, "wclient15")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]

    response = await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "drop", "reps": 6, "loadValue": "30", "loadUnitKey": "lb"},
    )
    assert response.status_code == 201
    assert response.json()["setType"] == "drop"


@pytest.mark.asyncio
async def test_reopening_completed_set_clears_completed_at(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient16", "client")
    await db_session.commit()
    token = await login(client, "wclient16")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]
    add_set_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "reps": 8, "loadValue": "50", "loadUnitKey": "lb"},
    )
    set_id = add_set_response.json()["id"]

    complete_response = await client.patch(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets/{set_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"completed": True},
    )
    assert complete_response.json()["completedAt"] is not None

    reopen_response = await client.patch(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets/{set_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"completed": False},
    )
    assert reopen_response.json()["completedAt"] is None


@pytest.mark.asyncio
async def test_session_with_no_completed_sets_cannot_be_completed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient17", "client")
    await db_session.commit()
    token = await login(client, "wclient17")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]
    await client.post(
        f"/api/me/workouts/{session_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "reps": 8},
    )

    response = await client.post(
        f"/api/me/workouts/{session_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "WORKOUT_HAS_NO_COMPLETED_SETS"


@pytest.mark.asyncio
async def test_complete_prunes_incomplete_sets_and_empty_exercises(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient18", "client")
    await db_session.commit()
    token = await login(client, "wclient18")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]

    bench_id = await _get_exercise_id(db_session, "barbell-bench-press")
    squat_id = await _get_exercise_id(db_session, "barbell-back-squat")

    bench_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": bench_id},
    )
    bench_session_exercise_id = bench_response.json()["id"]

    squat_response = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": squat_id},
    )
    squat_session_exercise_id = squat_response.json()["id"]

    completed_set = await client.post(
        f"/api/me/workouts/{session_id}/exercises/{bench_session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "reps": 8, "loadValue": "45", "loadUnitKey": "lb"},
    )
    await client.patch(
        f"/api/me/workouts/{session_id}/exercises/{bench_session_exercise_id}/sets/{completed_set.json()['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"completed": True},
    )
    await client.post(
        f"/api/me/workouts/{session_id}/exercises/{bench_session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "reps": 8},
    )
    await client.post(
        f"/api/me/workouts/{session_id}/exercises/{squat_session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal"},
    )

    complete_response = await client.post(
        f"/api/me/workouts/{session_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"notes": "Solid session"},
    )
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["status"] == "completed"
    assert completed["completedAt"] is not None
    assert len(completed["exercises"]) == 1
    assert len(completed["exercises"][0]["sets"]) == 1
    assert completed["exercises"][0]["sets"][0]["completedAt"] is not None

    idempotent_response = await client.post(
        f"/api/me/workouts/{session_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert idempotent_response.status_code == 200
    assert idempotent_response.json()["id"] == completed["id"]

    mutation_after_completion = await client.post(
        f"/api/me/workouts/{session_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": bench_id},
    )
    assert mutation_after_completion.status_code == 409
    assert mutation_after_completion.json()["error"]["code"] == "WORKOUT_ALREADY_COMPLETED"

    history_response = await client.get(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}
    )
    assert len(history_response.json()["items"]) == 1
    assert history_response.json()["items"][0]["completedSetCount"] == 1


@pytest.mark.asyncio
async def test_discard_deletes_session_and_completed_cannot_be_discarded(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "wclient19", "client")
    await db_session.commit()
    token = await login(client, "wclient19")

    start = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session_id = start.json()["id"]

    discard_response = await client.delete(
        f"/api/me/workouts/{session_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert discard_response.status_code == 204

    detail_response = await client.get(
        f"/api/me/workouts/{session_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert detail_response.status_code == 404

    # A completed session cannot be discarded.
    start2 = await client.post(
        "/api/me/workouts", headers={"Authorization": f"Bearer {token}"}, json={"mode": "freestyle"}
    )
    session2_id = start2.json()["id"]
    exercise_id = await _get_exercise_id(db_session, "plank")
    add_exercise_response = await client.post(
        f"/api/me/workouts/{session2_id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
        json={"exerciseId": exercise_id},
    )
    session_exercise_id = add_exercise_response.json()["id"]
    set_response = await client.post(
        f"/api/me/workouts/{session2_id}/exercises/{session_exercise_id}/sets",
        headers={"Authorization": f"Bearer {token}"},
        json={"setType": "normal", "durationSeconds": 60},
    )
    await client.patch(
        f"/api/me/workouts/{session2_id}/exercises/{session_exercise_id}/sets/{set_response.json()['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"completed": True},
    )
    await client.post(
        f"/api/me/workouts/{session2_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    discard_completed_response = await client.delete(
        f"/api/me/workouts/{session2_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert discard_completed_response.status_code == 409
    assert discard_completed_response.json()["error"]["code"] == "WORKOUT_ALREADY_COMPLETED"
