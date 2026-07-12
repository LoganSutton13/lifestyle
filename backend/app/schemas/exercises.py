from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

TRACKING_TYPES = {"reps_load", "reps_only", "duration"}


class EquipmentInfo(BaseModel):
    key: str
    display_name: str = Field(alias="displayName")

    model_config = {"populate_by_name": True}


class MuscleGroupInfo(BaseModel):
    key: str
    display_name: str = Field(alias="displayName")

    model_config = {"populate_by_name": True}


class ExerciseResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    equipment: EquipmentInfo
    tracking_type: str = Field(alias="trackingType")
    default_unilateral: bool = Field(alias="defaultUnilateral")
    default_rest_seconds: int = Field(alias="defaultRestSeconds")
    instructions: str
    primary_muscles: list[MuscleGroupInfo] = Field(alias="primaryMuscles")
    secondary_muscles: list[MuscleGroupInfo] = Field(alias="secondaryMuscles")
    archived_at: datetime | None = Field(alias="archivedAt")
    created_by_user_id: UUID | None = Field(default=None, alias="createdByUserId")

    model_config = {"populate_by_name": True}


class ExerciseListResponse(BaseModel):
    items: list[ExerciseResponse]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = {"populate_by_name": True}


class ExerciseSuggestionsResponse(BaseModel):
    items: list[ExerciseResponse]


class ExerciseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    equipment_key: str = Field(alias="equipmentKey")
    tracking_type: str = Field(alias="trackingType")
    default_unilateral: bool = Field(default=False, alias="defaultUnilateral")
    default_rest_seconds: int = Field(default=120, ge=0, le=3600, alias="defaultRestSeconds")
    primary_muscle_keys: list[str] = Field(alias="primaryMuscleKeys")
    secondary_muscle_keys: list[str] = Field(default_factory=list, alias="secondaryMuscleKeys")
    instructions: str = Field(default="", max_length=5000)

    model_config = {"populate_by_name": True}

    @field_validator("tracking_type")
    @classmethod
    def validate_tracking_type(cls, value: str) -> str:
        if value not in TRACKING_TYPES:
            msg = f"trackingType must be one of {sorted(TRACKING_TYPES)}"
            raise ValueError(msg)
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value


class ExerciseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    equipment_key: str | None = Field(default=None, alias="equipmentKey")
    tracking_type: str | None = Field(default=None, alias="trackingType")
    default_unilateral: bool | None = Field(default=None, alias="defaultUnilateral")
    default_rest_seconds: int | None = Field(default=None, ge=0, le=3600, alias="defaultRestSeconds")
    primary_muscle_keys: list[str] | None = Field(default=None, alias="primaryMuscleKeys")
    secondary_muscle_keys: list[str] | None = Field(default=None, alias="secondaryMuscleKeys")
    instructions: str | None = Field(default=None, max_length=5000)

    model_config = {"populate_by_name": True}

    @field_validator("tracking_type")
    @classmethod
    def validate_tracking_type(cls, value: str | None) -> str | None:
        if value is not None and value not in TRACKING_TYPES:
            msg = f"trackingType must be one of {sorted(TRACKING_TYPES)}"
            raise ValueError(msg)
        return value
