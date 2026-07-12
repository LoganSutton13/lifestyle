import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, Text, func
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint(
            "tracking_type IN ('reps_load', 'reps_only', 'duration')",
            name="ck_exercises_tracking_type",
        ),
        CheckConstraint(
            "default_rest_seconds >= 0 AND default_rest_seconds <= 3600",
            name="ck_exercises_default_rest_seconds",
        ),
        Index("idx_exercises_archived_normalized_name", "archived_at", "normalized_name"),
        Index("idx_exercises_equipment_archived", "equipment_key", "archived_at"),
        Index("idx_exercises_created_by_user_id", "created_by_user_id"),
        Index("uq_exercises_slug", "slug", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)
    equipment_key: Mapped[str] = mapped_column(
        Text, ForeignKey("exercise_equipment.key"), nullable=False
    )
    tracking_type: Mapped[str] = mapped_column(Text, nullable=False)
    default_unilateral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_rest_seconds: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=120)
    instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ExerciseMuscleGroup(Base):
    __tablename__ = "exercise_muscle_groups"

    exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )
    muscle_group_key: Mapped[str] = mapped_column(
        Text, ForeignKey("muscle_groups.key"), primary_key=True
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
