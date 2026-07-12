from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.exercises import ExerciseSuggestionsResponse
from app.schemas.workouts import (
    ActiveWorkoutResponse,
    AddExerciseRequest,
    AddSetRequest,
    AssignmentListItem,
    AssignmentListResponse,
    CompleteWorkoutRequest,
    ExerciseOrderRequest,
    SessionExerciseResponse,
    SessionUpdateRequest,
    StartWorkoutRequest,
    UpdateSessionExerciseRequest,
    UpdateSetRequest,
    WorkoutHistoryListResponse,
    WorkoutSessionDetailResponse,
    WorkoutSetResponse,
)
from app.services.exercise_service import ExerciseService
from app.services.workout_service import WorkoutService

router = APIRouter()


@router.get("/workouts/active", response_model=ActiveWorkoutResponse)
async def get_active_workout(
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActiveWorkoutResponse:
    service = WorkoutService(db)
    return await service.get_active(current_user.id)


@router.post("/workouts", response_model=WorkoutSessionDetailResponse, status_code=201)
async def start_workout(
    data: StartWorkoutRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkoutSessionDetailResponse:
    service = WorkoutService(db)
    return await service.start_workout(current_user.id, data)


@router.get("/workouts", response_model=WorkoutHistoryListResponse)
async def list_workout_history(
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    page_size: int = Query(default=20, ge=1, le=50, alias="pageSize"),
) -> WorkoutHistoryListResponse:
    service = WorkoutService(db)
    return await service.list_history(current_user.id, cursor, page_size)


@router.get("/exercises/suggestions", response_model=ExerciseSuggestionsResponse)
async def get_exercise_suggestions(
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    session_id: UUID = Query(alias="sessionId"),
    limit: int = Query(default=3, ge=1, le=3),
) -> ExerciseSuggestionsResponse:
    service = ExerciseService(db)
    return await service.get_suggestions(current_user.id, session_id, limit)


@router.get("/workout-assignments", response_model=AssignmentListResponse)
async def list_workout_assignments(
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    state: str | None = None,
    cursor: str | None = None,
    page_size: int = Query(default=20, ge=1, le=50, alias="pageSize"),
) -> AssignmentListResponse:
    service = WorkoutService(db)
    return await service.list_assignments(current_user.id, state, cursor, page_size)


@router.get("/workout-assignments/{assignment_id}", response_model=AssignmentListItem)
async def get_workout_assignment(
    assignment_id: UUID,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignmentListItem:
    service = WorkoutService(db)
    return await service.get_assignment_detail(current_user.id, assignment_id)


@router.get("/workouts/{session_id}", response_model=WorkoutSessionDetailResponse)
async def get_workout_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkoutSessionDetailResponse:
    service = WorkoutService(db)
    return await service.get_session_detail(current_user.id, session_id)


@router.patch("/workouts/{session_id}", response_model=WorkoutSessionDetailResponse)
async def update_workout_session(
    session_id: UUID,
    data: SessionUpdateRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkoutSessionDetailResponse:
    service = WorkoutService(db)
    return await service.update_session_metadata(current_user.id, session_id, data)


@router.delete("/workouts/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def discard_workout_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = WorkoutService(db)
    await service.discard_workout(current_user.id, session_id)


@router.post("/workouts/{session_id}/complete", response_model=WorkoutSessionDetailResponse)
async def complete_workout_session(
    session_id: UUID,
    data: CompleteWorkoutRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkoutSessionDetailResponse:
    service = WorkoutService(db)
    return await service.complete_workout(current_user.id, session_id, data)


@router.post("/workouts/{session_id}/exercises", response_model=SessionExerciseResponse, status_code=201)
async def add_workout_exercise(
    session_id: UUID,
    data: AddExerciseRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionExerciseResponse:
    service = WorkoutService(db)
    return await service.add_exercise(current_user.id, session_id, data)


@router.patch(
    "/workouts/{session_id}/exercises/{session_exercise_id}", response_model=SessionExerciseResponse
)
async def update_workout_exercise(
    session_id: UUID,
    session_exercise_id: UUID,
    data: UpdateSessionExerciseRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionExerciseResponse:
    service = WorkoutService(db)
    return await service.update_session_exercise(current_user.id, session_id, session_exercise_id, data)


@router.delete(
    "/workouts/{session_id}/exercises/{session_exercise_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_workout_exercise(
    session_id: UUID,
    session_exercise_id: UUID,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = WorkoutService(db)
    await service.remove_session_exercise(current_user.id, session_id, session_exercise_id)


@router.put("/workouts/{session_id}/exercise-order", response_model=list[SessionExerciseResponse])
async def reorder_workout_exercises(
    session_id: UUID,
    data: ExerciseOrderRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SessionExerciseResponse]:
    service = WorkoutService(db)
    return await service.reorder_exercises(current_user.id, session_id, data)


@router.post(
    "/workouts/{session_id}/exercises/{session_exercise_id}/sets",
    response_model=WorkoutSetResponse,
    status_code=201,
)
async def add_workout_set(
    session_id: UUID,
    session_exercise_id: UUID,
    data: AddSetRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkoutSetResponse:
    service = WorkoutService(db)
    return await service.add_set(current_user.id, session_id, session_exercise_id, data)


@router.patch(
    "/workouts/{session_id}/exercises/{session_exercise_id}/sets/{set_id}",
    response_model=WorkoutSetResponse,
)
async def update_workout_set(
    session_id: UUID,
    session_exercise_id: UUID,
    set_id: UUID,
    data: UpdateSetRequest,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkoutSetResponse:
    service = WorkoutService(db)
    return await service.update_set(current_user.id, session_id, session_exercise_id, set_id, data)


@router.delete(
    "/workouts/{session_id}/exercises/{session_exercise_id}/sets/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workout_set(
    session_id: UUID,
    session_exercise_id: UUID,
    set_id: UUID,
    current_user: Annotated[User, Depends(require_roles("client"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = WorkoutService(db)
    await service.delete_set(current_user.id, session_id, session_exercise_id, set_id)
