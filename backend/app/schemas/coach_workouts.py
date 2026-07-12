from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.workouts import SET_TYPES


class TemplateSetInput(BaseModel):
    position: int = Field(ge=0)
    set_type: str = Field(default="normal", alias="setType")
    target_reps_min: int | None = Field(default=None, ge=1, le=1000, alias="targetRepsMin")
    target_reps_max: int | None = Field(default=None, ge=1, le=1000, alias="targetRepsMax")
    target_load_value: Decimal | None = Field(default=None, ge=0, alias="targetLoadValue")
    target_load_unit_key: str | None = Field(default=None, alias="targetLoadUnitKey")
    target_duration_seconds: int | None = Field(default=None, ge=1, le=86400, alias="targetDurationSeconds")
    target_rpe: Decimal | None = Field(default=None, ge=0, le=10, alias="targetRpe")
    notes: str = Field(default="", max_length=10000)

    model_config = {"populate_by_name": True}

    @field_validator("set_type")
    @classmethod
    def validate_set_type(cls, value: str) -> str:
        if value not in SET_TYPES:
            msg = f"setType must be one of {sorted(SET_TYPES)}"
            raise ValueError(msg)
        return value


class TemplateExerciseInput(BaseModel):
    position: int = Field(ge=0)
    exercise_id: UUID = Field(alias="exerciseId")
    is_unilateral: bool = Field(default=False, alias="isUnilateral")
    rest_seconds: int = Field(default=120, ge=0, le=3600, alias="restSeconds")
    notes: str = Field(default="", max_length=10000)
    sets: list[TemplateSetInput] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class TemplateDraftUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    notes: str = Field(default="", max_length=10000)
    exercises: list[TemplateExerciseInput] = Field(default_factory=list)


class TemplateCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    notes: str = Field(default="", max_length=10000)


class TemplateSetResponse(BaseModel):
    id: UUID
    position: int
    set_type: str = Field(alias="setType")
    target_reps_min: int | None = Field(default=None, alias="targetRepsMin")
    target_reps_max: int | None = Field(default=None, alias="targetRepsMax")
    target_load_value: str | None = Field(default=None, alias="targetLoadValue")
    target_load_unit_key: str | None = Field(default=None, alias="targetLoadUnitKey")
    target_duration_seconds: int | None = Field(default=None, alias="targetDurationSeconds")
    target_rpe: str | None = Field(default=None, alias="targetRpe")
    notes: str

    model_config = {"populate_by_name": True}


class TemplateExerciseResponse(BaseModel):
    id: UUID
    position: int
    exercise_id: UUID = Field(alias="exerciseId")
    exercise_name: str = Field(alias="exerciseName")
    is_unilateral: bool = Field(alias="isUnilateral")
    rest_seconds: int = Field(alias="restSeconds")
    notes: str
    sets: list[TemplateSetResponse]

    model_config = {"populate_by_name": True}


class TemplateVersionResponse(BaseModel):
    id: UUID
    version_number: int = Field(alias="versionNumber")
    title: str
    notes: str
    status: str
    created_at: datetime = Field(alias="createdAt")
    published_at: datetime | None = Field(default=None, alias="publishedAt")
    exercises: list[TemplateExerciseResponse]

    model_config = {"populate_by_name": True}


class TemplateListItem(BaseModel):
    id: UUID
    archived_at: datetime | None = Field(default=None, alias="archivedAt")
    updated_at: datetime = Field(alias="updatedAt")
    title: str
    has_draft: bool = Field(alias="hasDraft")
    latest_published_version_number: int | None = Field(default=None, alias="latestPublishedVersionNumber")

    model_config = {"populate_by_name": True}


class TemplateListResponse(BaseModel):
    items: list[TemplateListItem]


class TemplateDetailResponse(BaseModel):
    id: UUID
    coach_id: UUID = Field(alias="coachId")
    archived_at: datetime | None = Field(default=None, alias="archivedAt")
    versions: list[TemplateVersionResponse]

    model_config = {"populate_by_name": True}


class AssignmentCreateRequest(BaseModel):
    template_version_id: UUID = Field(alias="templateVersionId")
    scheduled_for: date | None = Field(default=None, alias="scheduledFor")
    due_at: datetime | None = Field(default=None, alias="dueAt")
    notes: str = Field(default="", max_length=10000)

    model_config = {"populate_by_name": True}
