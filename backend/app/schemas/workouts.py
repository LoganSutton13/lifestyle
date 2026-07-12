from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.exercises import EquipmentInfo

SET_TYPES = {"normal", "warmup", "drop", "failure"}


class ExerciseSummary(BaseModel):
    id: UUID
    name: str
    tracking_type: str = Field(alias="trackingType")
    equipment: EquipmentInfo

    model_config = {"populate_by_name": True}


class WorkoutSetResponse(BaseModel):
    id: UUID
    position: int
    set_type: str = Field(alias="setType")
    reps: int | None = None
    load_value: str | None = Field(default=None, alias="loadValue")
    load_unit_key: str | None = Field(default=None, alias="loadUnitKey")
    duration_seconds: int | None = Field(default=None, alias="durationSeconds")
    rpe: str | None = None
    completed_at: datetime | None = Field(default=None, alias="completedAt")

    model_config = {"populate_by_name": True}


class PrescriptionSetResponse(BaseModel):
    id: UUID
    position: int
    set_type: str = Field(alias="setType")
    target_reps_min: int | None = Field(default=None, alias="targetRepsMin")
    target_reps_max: int | None = Field(default=None, alias="targetRepsMax")
    target_load_value: str | None = Field(default=None, alias="targetLoadValue")
    target_load_unit_key: str | None = Field(default=None, alias="targetLoadUnitKey")
    target_duration_seconds: int | None = Field(default=None, alias="targetDurationSeconds")
    target_rpe: str | None = Field(default=None, alias="targetRpe")

    model_config = {"populate_by_name": True}


class PrescriptionResponse(BaseModel):
    notes: str
    sets: list[PrescriptionSetResponse]


class SessionExerciseResponse(BaseModel):
    id: UUID
    position: int
    is_unilateral: bool = Field(alias="isUnilateral")
    rest_seconds: int = Field(alias="restSeconds")
    notes: str
    exercise: ExerciseSummary
    prescription: PrescriptionResponse | None = None
    sets: list[WorkoutSetResponse]

    model_config = {"populate_by_name": True}


class AssignmentRefResponse(BaseModel):
    id: UUID
    scheduled_for: date | None = Field(default=None, alias="scheduledFor")
    template_version_id: UUID = Field(alias="templateVersionId")

    model_config = {"populate_by_name": True}


class WorkoutSessionDetailResponse(BaseModel):
    id: UUID
    source: str
    status: str
    title: str | None = None
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    notes: str
    assignment: AssignmentRefResponse | None = None
    exercises: list[SessionExerciseResponse]

    model_config = {"populate_by_name": True}


class ActiveWorkoutResponse(BaseModel):
    session: WorkoutSessionDetailResponse | None = None


class StartWorkoutRequest(BaseModel):
    mode: Literal["freestyle", "assigned"]
    assignment_id: UUID | None = Field(default=None, alias="assignmentId")

    model_config = {"populate_by_name": True}


class SessionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=10000)


class AddExerciseRequest(BaseModel):
    exercise_id: UUID = Field(alias="exerciseId")

    model_config = {"populate_by_name": True}


class UpdateSessionExerciseRequest(BaseModel):
    is_unilateral: bool | None = Field(default=None, alias="isUnilateral")
    rest_seconds: int | None = Field(default=None, ge=0, le=3600, alias="restSeconds")
    notes: str | None = Field(default=None, max_length=10000)

    model_config = {"populate_by_name": True}


class ExerciseOrderRequest(BaseModel):
    exercise_ids: list[UUID] = Field(alias="exerciseIds")

    model_config = {"populate_by_name": True}


def _validate_set_type(value: str | None) -> str | None:
    if value is not None and value not in SET_TYPES:
        msg = f"setType must be one of {sorted(SET_TYPES)}"
        raise ValueError(msg)
    return value


class AddSetRequest(BaseModel):
    set_type: str = Field(default="normal", alias="setType")
    reps: int | None = Field(default=None, ge=0, le=1000)
    load_value: Decimal | None = Field(default=None, alias="loadValue")
    load_unit_key: str | None = Field(default=None, alias="loadUnitKey")
    duration_seconds: int | None = Field(default=None, ge=0, le=86400, alias="durationSeconds")
    rpe: Decimal | None = Field(default=None, ge=0, le=10)

    model_config = {"populate_by_name": True}

    @field_validator("set_type")
    @classmethod
    def validate_set_type(cls, value: str) -> str:
        return _validate_set_type(value)

    @field_validator("load_value")
    @classmethod
    def validate_load_value(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("loadValue must not be negative")
        return value


class UpdateSetRequest(BaseModel):
    set_type: str | None = Field(default=None, alias="setType")
    reps: int | None = Field(default=None, ge=0, le=1000)
    load_value: Decimal | None = Field(default=None, alias="loadValue")
    load_unit_key: str | None = Field(default=None, alias="loadUnitKey")
    duration_seconds: int | None = Field(default=None, ge=0, le=86400, alias="durationSeconds")
    rpe: Decimal | None = Field(default=None, ge=0, le=10)
    completed: bool | None = None

    model_config = {"populate_by_name": True}

    @field_validator("set_type")
    @classmethod
    def validate_set_type(cls, value: str | None) -> str | None:
        return _validate_set_type(value)

    @field_validator("load_value")
    @classmethod
    def validate_load_value(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("loadValue must not be negative")
        return value


class CompleteWorkoutRequest(BaseModel):
    discard_incomplete_sets: bool = Field(default=True, alias="discardIncompleteSets")
    notes: str | None = Field(default=None, max_length=10000)

    model_config = {"populate_by_name": True}


class WorkoutHistoryItem(BaseModel):
    id: UUID
    source: str
    title: str | None = None
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime = Field(alias="completedAt")
    duration_seconds: int = Field(alias="durationSeconds")
    exercise_count: int = Field(alias="exerciseCount")
    completed_set_count: int = Field(alias="completedSetCount")

    model_config = {"populate_by_name": True}


class WorkoutHistoryListResponse(BaseModel):
    items: list[WorkoutHistoryItem]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = {"populate_by_name": True}


class AssignmentListItem(BaseModel):
    id: UUID
    template_version_id: UUID = Field(alias="templateVersionId")
    title: str
    coach_name: str = Field(alias="coachName")
    scheduled_for: date | None = Field(default=None, alias="scheduledFor")
    due_at: datetime | None = Field(default=None, alias="dueAt")
    notes: str
    exercise_count: int = Field(alias="exerciseCount")
    state: Literal["available", "in_progress", "completed"]
    assigned_at: datetime = Field(alias="assignedAt")
    session_id: UUID | None = Field(default=None, alias="sessionId")

    model_config = {"populate_by_name": True}


class AssignmentListResponse(BaseModel):
    items: list[AssignmentListItem]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = {"populate_by_name": True}
