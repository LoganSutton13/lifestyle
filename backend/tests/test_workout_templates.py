import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.coach_client import CoachClient
from app.db.models.exercise import Exercise
from tests.conftest import create_user, login


async def _get_exercise_id(db_session: AsyncSession, slug: str) -> str:
    result = await db_session.execute(select(Exercise).where(Exercise.slug == slug))
    exercise = result.scalar_one()
    return str(exercise.id)


async def _create_and_publish_template(
    client: AsyncClient, coach_token: str, exercise_id: str, title: str = "Upper Body Day"
) -> tuple[str, str]:
    create_response = await client.post(
        "/api/coach/workout-templates",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"title": title, "notes": "Focus on form"},
    )
    assert create_response.status_code == 201
    template = create_response.json()
    template_id = template["id"]
    draft_version = template["versions"][0]
    version_id = draft_version["id"]

    update_response = await client.put(
        f"/api/coach/workout-template-versions/{version_id}",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "title": title,
            "notes": "Focus on form",
            "exercises": [
                {
                    "position": 0,
                    "exerciseId": exercise_id,
                    "isUnilateral": False,
                    "restSeconds": 90,
                    "notes": "Keep two reps in reserve.",
                    "sets": [
                        {
                            "position": 0,
                            "setType": "normal",
                            "targetRepsMin": 8,
                            "targetRepsMax": 10,
                        }
                    ],
                }
            ],
        },
    )
    assert update_response.status_code == 200

    publish_response = await client.post(
        f"/api/coach/workout-template-versions/{version_id}/publish",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"
    return template_id, version_id


@pytest.mark.asyncio
async def test_coach_can_create_draft_template(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "tcoach1", "coach")
    await db_session.commit()
    token = await login(client, "tcoach1")

    response = await client.post(
        "/api/coach/workout-templates",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Leg Day", "notes": ""},
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["versions"]) == 1
    assert data["versions"][0]["status"] == "draft"
    assert data["versions"][0]["versionNumber"] == 1


@pytest.mark.asyncio
async def test_published_template_is_immutable(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user(db_session, "tcoach2", "coach")
    await db_session.commit()
    token = await login(client, "tcoach2")
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")

    _, version_id = await _create_and_publish_template(client, token, exercise_id)

    response = await client.put(
        f"/api/coach/workout-template-versions/{version_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Changed", "notes": "", "exercises": []},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TEMPLATE_VERSION_IMMUTABLE"

    republish_response = await client.post(
        f"/api/coach/workout-template-versions/{version_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert republish_response.status_code == 409


@pytest.mark.asyncio
async def test_editing_published_template_creates_new_version(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "tcoach3", "coach")
    await db_session.commit()
    token = await login(client, "tcoach3")
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")

    template_id, v1_id = await _create_and_publish_template(client, token, exercise_id)

    draft_response = await client.post(
        f"/api/coach/workout-templates/{template_id}/draft",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert draft["status"] == "draft"
    assert draft["versionNumber"] == 2
    assert draft["id"] != v1_id
    # Cloned content from the published version.
    assert len(draft["exercises"]) == 1

    idempotent_draft_response = await client.post(
        f"/api/coach/workout-templates/{template_id}/draft",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert idempotent_draft_response.json()["id"] == draft["id"]


@pytest.mark.asyncio
async def test_assignment_references_published_version_and_template_edits_dont_affect_it(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "tcoach4", "coach")
    client_user = await create_user(db_session, "tclient1", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    coach_token = await login(client, "tcoach4")
    client_token = await login(client, "tclient1")
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")

    template_id, v1_id = await _create_and_publish_template(client, coach_token, exercise_id)

    assign_response = await client.post(
        f"/api/coach/clients/{client_user.id}/workout-assignments",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"templateVersionId": v1_id},
    )
    assert assign_response.status_code == 201
    assignment_id = assign_response.json()["id"]
    assert assign_response.json()["templateVersionId"] == v1_id

    # Coach edits the template into a new version after assigning v1.
    await client.post(
        f"/api/coach/workout-templates/{template_id}/draft",
        headers={"Authorization": f"Bearer {coach_token}"},
    )

    start_response = await client.post(
        "/api/me/workouts",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"mode": "assigned", "assignmentId": assignment_id},
    )
    assert start_response.status_code == 201
    session = start_response.json()
    assert session["assignment"]["templateVersionId"] == v1_id
    assert len(session["exercises"]) == 1
    assert session["exercises"][0]["prescription"]["sets"][0]["targetRepsMin"] == 8


@pytest.mark.asyncio
async def test_coach_cannot_assign_to_unassociated_client(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "tcoach5", "coach")
    client_user = await create_user(db_session, "tclient2", "client")
    await db_session.commit()
    coach_token = await login(client, "tcoach5")
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    _, version_id = await _create_and_publish_template(client, coach_token, exercise_id)

    response = await client.post(
        f"/api/coach/clients/{client_user.id}/workout-assignments",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"templateVersionId": version_id},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_one_assignment_cannot_create_two_sessions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "tcoach6", "coach")
    client_user = await create_user(db_session, "tclient3", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    coach_token = await login(client, "tcoach6")
    client_token = await login(client, "tclient3")
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    _, version_id = await _create_and_publish_template(client, coach_token, exercise_id)

    assign_response = await client.post(
        f"/api/coach/clients/{client_user.id}/workout-assignments",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"templateVersionId": version_id},
    )
    assignment_id = assign_response.json()["id"]

    first_start = await client.post(
        "/api/me/workouts",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"mode": "assigned", "assignmentId": assignment_id},
    )
    assert first_start.status_code == 201
    session_id = first_start.json()["id"]

    # Starting again while in progress is idempotent and returns the same session.
    second_start = await client.post(
        "/api/me/workouts",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"mode": "assigned", "assignmentId": assignment_id},
    )
    assert second_start.status_code == 201
    assert second_start.json()["id"] == session_id


@pytest.mark.asyncio
async def test_canceled_assignment_cannot_be_started(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "tcoach7", "coach")
    client_user = await create_user(db_session, "tclient4", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    coach_token = await login(client, "tcoach7")
    client_token = await login(client, "tclient4")
    exercise_id = await _get_exercise_id(db_session, "barbell-bench-press")
    _, version_id = await _create_and_publish_template(client, coach_token, exercise_id)

    assign_response = await client.post(
        f"/api/coach/clients/{client_user.id}/workout-assignments",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"templateVersionId": version_id},
    )
    assignment_id = assign_response.json()["id"]

    cancel_response = await client.post(
        f"/api/coach/clients/{client_user.id}/workout-assignments/{assignment_id}/cancel",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert cancel_response.status_code == 204

    start_response = await client.post(
        "/api/me/workouts",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"mode": "assigned", "assignmentId": assignment_id},
    )
    assert start_response.status_code == 409
    assert start_response.json()["error"]["code"] == "ASSIGNMENT_NOT_AVAILABLE"


@pytest.mark.asyncio
async def test_coach_can_read_associated_client_history_but_not_unassociated(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "tcoach8", "coach")
    other_coach = await create_user(db_session, "tcoach9", "coach")
    client_user = await create_user(db_session, "tclient5", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    coach_token = await login(client, "tcoach8")
    other_coach_token = await login(client, "tcoach9")

    good_response = await client.get(
        f"/api/coach/clients/{client_user.id}/workouts",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert good_response.status_code == 200

    bad_response = await client.get(
        f"/api/coach/clients/{client_user.id}/workouts",
        headers={"Authorization": f"Bearer {other_coach_token}"},
    )
    assert bad_response.status_code == 403


@pytest.mark.asyncio
async def test_starting_assignment_with_no_exercises_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    coach = await create_user(db_session, "tcoach10", "coach")
    client_user = await create_user(db_session, "tclient6", "client")
    db_session.add(CoachClient(coach_id=coach.id, client_id=client_user.id))
    await db_session.commit()
    coach_token = await login(client, "tcoach10")

    create_response = await client.post(
        "/api/coach/workout-templates",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"title": "Empty Template", "notes": ""},
    )
    version_id = create_response.json()["versions"][0]["id"]

    publish_response = await client.post(
        f"/api/coach/workout-template-versions/{version_id}/publish",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert publish_response.status_code == 400
