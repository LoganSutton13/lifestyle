import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"
    __table_args__ = (
        Index("idx_workout_templates_coach_archived_updated", "coach_id", "archived_at", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coach_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WorkoutTemplateVersion(Base):
    __tablename__ = "workout_template_versions"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published')", name="ck_workout_template_versions_status"),
        CheckConstraint("version_number >= 1", name="ck_workout_template_versions_number"),
        Index("uq_workout_template_versions_template_number", "template_id", "version_number", unique=True),
        Index(
            "uq_workout_template_one_draft",
            "template_id",
            unique=True,
            sqlite_where=text("status = 'draft'"),
            postgresql_where=text("status = 'draft'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workout_templates.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkoutTemplateExercise(Base):
    __tablename__ = "workout_template_exercises"
    __table_args__ = (
        CheckConstraint(
            "rest_seconds >= 0 AND rest_seconds <= 3600",
            name="ck_workout_template_exercises_rest",
        ),
        Index("uq_workout_template_exercises_version_position", "template_version_id", "position", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workout_template_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_unilateral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rest_seconds: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=120)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")


class WorkoutTemplateSet(Base):
    __tablename__ = "workout_template_sets"
    __table_args__ = (
        CheckConstraint(
            "set_type IN ('normal', 'warmup', 'drop', 'failure')",
            name="ck_workout_template_sets_type",
        ),
        Index("uq_workout_template_sets_exercise_position", "template_exercise_id", "position", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workout_template_exercises.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    set_type: Mapped[str] = mapped_column(Text, nullable=False, default="normal")
    target_reps_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_reps_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_load_value_input: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    target_load_unit_key: Mapped[str | None] = mapped_column(
        Text, ForeignKey("measurement_units.key"), nullable=True
    )
    target_load_value_base: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    target_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_rpe: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
