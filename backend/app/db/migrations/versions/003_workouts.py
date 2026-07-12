"""Add workout exercise tracking schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_workouts"
down_revision: Union[str, None] = "002_task_recurrence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exercise_equipment",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "muscle_groups",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("slug", postgresql.CITEXT(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("equipment_key", sa.Text(), sa.ForeignKey("exercise_equipment.key"), nullable=False),
        sa.Column("tracking_type", sa.Text(), nullable=False),
        sa.Column("default_unilateral", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("default_rest_seconds", sa.SmallInteger(), nullable=False, server_default="120"),
        sa.Column("instructions", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("tracking_type IN ('reps_load', 'reps_only', 'duration')", name="ck_exercises_tracking_type"),
        sa.CheckConstraint(
            "default_rest_seconds >= 0 AND default_rest_seconds <= 3600",
            name="ck_exercises_default_rest_seconds",
        ),
        sa.UniqueConstraint("slug", name="uq_exercises_slug"),
    )
    op.create_index("idx_exercises_archived_normalized_name", "exercises", ["archived_at", "normalized_name"])
    op.create_index("idx_exercises_equipment_archived", "exercises", ["equipment_key", "archived_at"])
    op.create_index("idx_exercises_created_by_user_id", "exercises", ["created_by_user_id"])

    op.create_table(
        "exercise_muscle_groups",
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("muscle_group_key", sa.Text(), sa.ForeignKey("muscle_groups.key"), primary_key=True),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("role IN ('primary', 'secondary')", name="ck_exercise_muscle_groups_role"),
    )

    op.create_table(
        "workout_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_workout_templates_coach_archived_updated", "workout_templates", ["coach_id", "archived_at", "updated_at"])

    op.create_table(
        "workout_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('draft', 'published')", name="ck_workout_template_versions_status"),
        sa.CheckConstraint("version_number >= 1", name="ck_workout_template_versions_number"),
        sa.UniqueConstraint("template_id", "version_number", name="uq_workout_template_versions_template_number"),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_workout_template_one_draft
        ON workout_template_versions(template_id)
        WHERE status = 'draft'
        """
    )

    op.create_table(
        "workout_template_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("template_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_template_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_unilateral", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rest_seconds", sa.SmallInteger(), nullable=False, server_default="120"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.CheckConstraint("rest_seconds >= 0 AND rest_seconds <= 3600", name="ck_workout_template_exercises_rest"),
        sa.UniqueConstraint("template_version_id", "position", name="uq_workout_template_exercises_version_position"),
    )

    op.create_table(
        "workout_template_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("template_exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_template_exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("set_type", sa.Text(), nullable=False, server_default="normal"),
        sa.Column("target_reps_min", sa.Integer(), nullable=True),
        sa.Column("target_reps_max", sa.Integer(), nullable=True),
        sa.Column("target_load_value_input", sa.Numeric(12, 4), nullable=True),
        sa.Column("target_load_unit_key", sa.Text(), sa.ForeignKey("measurement_units.key"), nullable=True),
        sa.Column("target_load_value_base", sa.Numeric(12, 4), nullable=True),
        sa.Column("target_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("target_rpe", sa.Numeric(4, 1), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.CheckConstraint("set_type IN ('normal', 'warmup', 'drop', 'failure')", name="ck_workout_template_sets_type"),
        sa.UniqueConstraint("template_exercise_id", "position", name="uq_workout_template_sets_exercise_position"),
    )

    op.create_table(
        "workout_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("template_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_template_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_for", sa.Date(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_workout_assignments_client_scheduled", "workout_assignments", ["client_id", "scheduled_for", "assigned_at"])
    op.create_index("idx_workout_assignments_assigned_by", "workout_assignments", ["assigned_by_user_id", "assigned_at"])

    op.create_table(
        "workout_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_assignments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="in_progress"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source IN ('freestyle', 'assigned')", name="ck_workout_sessions_source"),
        sa.CheckConstraint("status IN ('in_progress', 'completed')", name="ck_workout_sessions_status"),
        sa.CheckConstraint(
            "(status = 'in_progress' AND completed_at IS NULL) OR (status = 'completed' AND completed_at IS NOT NULL)",
            name="ck_workout_sessions_completed_at",
        ),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_workout_sessions_one_active
        ON workout_sessions(client_id)
        WHERE status = 'in_progress'
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_workout_sessions_assignment
        ON workout_sessions(assignment_id)
        WHERE assignment_id IS NOT NULL
        """
    )
    op.create_index("idx_workout_sessions_client_started", "workout_sessions", ["client_id", "started_at", "id"])

    op.create_table(
        "workout_session_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_template_exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_template_exercises.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_unilateral", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rest_seconds", sa.SmallInteger(), nullable=False, server_default="120"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rest_seconds >= 0 AND rest_seconds <= 3600", name="ck_workout_session_exercises_rest"),
        sa.UniqueConstraint("session_id", "position", name="uq_workout_session_exercises_position"),
    )
    op.create_index("idx_workout_session_exercises_exercise_id", "workout_session_exercises", ["exercise_id"])
    op.create_index("idx_workout_session_exercises_source_template", "workout_session_exercises", ["source_template_exercise_id"])

    op.create_table(
        "workout_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("session_exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_session_exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_template_set_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_template_sets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("set_type", sa.Text(), nullable=False, server_default="normal"),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("load_value_input", sa.Numeric(12, 4), nullable=True),
        sa.Column("load_unit_key", sa.Text(), sa.ForeignKey("measurement_units.key"), nullable=True),
        sa.Column("load_value_base", sa.Numeric(12, 4), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("rpe", sa.Numeric(4, 1), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("set_type IN ('normal', 'warmup', 'drop', 'failure')", name="ck_workout_sets_type"),
        sa.CheckConstraint("reps IS NULL OR (reps >= 0 AND reps <= 1000)", name="ck_workout_sets_reps"),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR (duration_seconds >= 0 AND duration_seconds <= 86400)",
            name="ck_workout_sets_duration",
        ),
        sa.UniqueConstraint("session_exercise_id", "position", name="uq_workout_sets_exercise_position"),
    )
    op.create_index("idx_workout_sets_completed_at", "workout_sets", ["completed_at"])

    for table in ("exercises", "workout_templates", "workout_sessions", "workout_session_exercises", "workout_sets"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
            """
        )


def downgrade() -> None:
    for table in ("workout_sets", "workout_session_exercises", "workout_sessions", "workout_templates", "exercises"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.drop_table("workout_sets")
    op.drop_table("workout_session_exercises")
    op.execute("DROP INDEX IF EXISTS uq_workout_sessions_assignment")
    op.execute("DROP INDEX IF EXISTS uq_workout_sessions_one_active")
    op.drop_table("workout_sessions")
    op.drop_table("workout_assignments")
    op.drop_table("workout_template_sets")
    op.drop_table("workout_template_exercises")
    op.execute("DROP INDEX IF EXISTS uq_workout_template_one_draft")
    op.drop_table("workout_template_versions")
    op.drop_table("workout_templates")
    op.drop_table("exercise_muscle_groups")
    op.drop_table("exercises")
    op.drop_table("muscle_groups")
    op.drop_table("exercise_equipment")
