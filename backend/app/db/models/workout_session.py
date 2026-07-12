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


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    __table_args__ = (
        CheckConstraint("source IN ('freestyle', 'assigned')", name="ck_workout_sessions_source"),
        CheckConstraint("status IN ('in_progress', 'completed')", name="ck_workout_sessions_status"),
        CheckConstraint(
            "(status = 'in_progress' AND completed_at IS NULL) OR "
            "(status = 'completed' AND completed_at IS NOT NULL)",
            name="ck_workout_sessions_completed_at",
        ),
        Index(
            "uq_workout_sessions_one_active",
            "client_id",
            unique=True,
            sqlite_where=text("status = 'in_progress'"),
            postgresql_where=text("status = 'in_progress'"),
        ),
        Index(
            "uq_workout_sessions_assignment",
            "assignment_id",
            unique=True,
            sqlite_where=text("assignment_id IS NOT NULL"),
            postgresql_where=text("assignment_id IS NOT NULL"),
        ),
        Index("idx_workout_sessions_client_started", "client_id", "started_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workout_assignments.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="in_progress")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WorkoutSessionExercise(Base):
    __tablename__ = "workout_session_exercises"
    __table_args__ = (
        CheckConstraint(
            "rest_seconds >= 0 AND rest_seconds <= 3600",
            name="ck_workout_session_exercises_rest",
        ),
        Index("uq_workout_session_exercises_position", "session_id", "position", unique=True),
        Index("idx_workout_session_exercises_exercise_id", "exercise_id"),
        Index("idx_workout_session_exercises_source_template", "source_template_exercise_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False
    )
    source_template_exercise_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workout_template_exercises.id", ondelete="SET NULL"),
        nullable=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_unilateral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rest_seconds: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=120)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    __table_args__ = (
        CheckConstraint(
            "set_type IN ('normal', 'warmup', 'drop', 'failure')",
            name="ck_workout_sets_type",
        ),
        CheckConstraint("reps IS NULL OR (reps >= 0 AND reps <= 1000)", name="ck_workout_sets_reps"),
        CheckConstraint(
            "duration_seconds IS NULL OR (duration_seconds >= 0 AND duration_seconds <= 86400)",
            name="ck_workout_sets_duration",
        ),
        Index("uq_workout_sets_exercise_position", "session_exercise_id", "position", unique=True),
        Index("idx_workout_sets_completed_at", "completed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workout_session_exercises.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_template_set_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workout_template_sets.id", ondelete="SET NULL"),
        nullable=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    set_type: Mapped[str] = mapped_column(Text, nullable=False, default="normal")
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_value_input: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    load_unit_key: Mapped[str | None] = mapped_column(
        Text, ForeignKey("measurement_units.key"), nullable=True
    )
    load_value_base: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rpe: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
