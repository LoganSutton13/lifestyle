"""Initial database schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("username", postgresql.CITEXT(), nullable=False),
        sa.Column("first_name", sa.Text(), nullable=False),
        sa.Column("last_name", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("avatar_key", sa.Text(), server_default="avocado", nullable=False),
        sa.Column("timezone", sa.Text(), server_default="America/Los_Angeles", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('client', 'coach', 'admin')", name="ck_users_role"),
        sa.CheckConstraint("char_length(first_name) BETWEEN 1 AND 80", name="ck_users_first_name"),
        sa.CheckConstraint("char_length(last_name) BETWEEN 1 AND 80", name="ck_users_last_name"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_created_at", "users", ["created_at"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_hash", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("idx_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.create_table(
        "coach_clients",
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("coach_id <> client_id", name="ck_coach_clients_not_self"),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("coach_id", "client_id"),
    )
    op.create_index("idx_coach_clients_client_id", "coach_clients", ["client_id"])

    op.create_table(
        "meal_categories",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "measurement_units",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("dimension", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("system", sa.Text(), nullable=False),
        sa.Column("to_base_multiplier", sa.Numeric(18, 10), server_default="1", nullable=False),
        sa.Column("to_base_offset", sa.Numeric(18, 10), server_default="0", nullable=False),
        sa.CheckConstraint("dimension IN ('weight', 'length', 'count')", name="ck_measurement_units_dimension"),
        sa.CheckConstraint("system IN ('imperial', 'metric', 'none')", name="ck_measurement_units_system"),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "measurement_types",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("dimension", sa.Text(), nullable=False),
        sa.Column("default_unit_key", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.CheckConstraint("dimension IN ('weight', 'length', 'count')", name="ck_measurement_types_dimension"),
        sa.ForeignKeyConstraint(["default_unit_key"], ["measurement_units.key"]),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "meals",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category_key", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("char_length(name) BETWEEN 1 AND 160", name="ck_meals_name"),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_key"], ["meal_categories.key"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_meals_coach_id", "meals", ["coach_id"])
    op.create_index("idx_meals_category_key", "meals", ["category_key"])
    op.create_index("idx_meals_created_at", "meals", ["created_at"])

    op.create_table(
        "meal_assignments",
        sa.Column("meal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by_coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["meal_id"], ["meals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by_coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("meal_id", "client_id"),
    )
    op.create_index("idx_meal_assignments_client_assigned_at", "meal_assignments", ["client_id", "assigned_at"])

    op.create_table(
        "measurement_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("measurement_type_key", sa.Text(), nullable=False),
        sa.Column("value_input", sa.Numeric(12, 4), nullable=False),
        sa.Column("unit_key", sa.Text(), nullable=False),
        sa.Column("value_base", sa.Numeric(12, 4), nullable=False),
        sa.Column("source", sa.Text(), server_default="manual", nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("value_input > 0", name="ck_measurement_records_value_input"),
        sa.CheckConstraint("value_base > 0", name="ck_measurement_records_value_base"),
        sa.CheckConstraint(
            "source IN ('manual', 'coach_entered', 'health_connect', 'samsung_health')",
            name="ck_measurement_records_source",
        ),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["measurement_type_key"], ["measurement_types.key"]),
        sa.ForeignKeyConstraint(["unit_key"], ["measurement_units.key"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_measurement_records_client_type_recorded",
        "measurement_records",
        ["client_id", "measurement_type_key", "recorded_at"],
    )
    op.create_index("idx_measurement_records_client_recorded", "measurement_records", ["client_id", "recorded_at"])

    op.create_table(
        "assigned_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("active_from", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("active_until", sa.Date(), nullable=True),
        sa.Column("repeats_daily", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("char_length(title) BETWEEN 1 AND 160", name="ck_assigned_tasks_title"),
        sa.CheckConstraint("active_until IS NULL OR active_until >= active_from", name="ck_assigned_tasks_dates"),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_assigned_tasks_client_active",
        "assigned_tasks",
        ["client_id", "active_from", "active_until", "archived_at"],
    )
    op.create_index("idx_assigned_tasks_coach", "assigned_tasks", ["coach_id"])

    op.create_table(
        "task_completions",
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["assigned_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "completion_date"),
    )
    op.create_index("idx_task_completions_client_date", "task_completions", ["client_id", "completion_date"])

    op.create_table(
        "daily_notes",
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note_date", sa.Date(), nullable=False),
        sa.Column("body", sa.Text(), server_default="", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("client_id", "note_date"),
    )
    op.create_index("idx_daily_notes_client_date", "daily_notes", ["client_id", "note_date"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("idx_audit_logs_actor", "audit_logs", ["actor_user_id"])
    op.create_index("idx_audit_logs_target", "audit_logs", ["target_user_id"])

    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    for table in ("users", "meals", "assigned_tasks"):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)


def downgrade() -> None:
    for table in ("assigned_tasks", "meals", "users"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
    op.drop_table("audit_logs")
    op.drop_table("daily_notes")
    op.drop_table("task_completions")
    op.drop_table("assigned_tasks")
    op.drop_table("measurement_records")
    op.drop_table("meal_assignments")
    op.drop_table("meals")
    op.drop_table("measurement_types")
    op.drop_table("measurement_units")
    op.drop_table("meal_categories")
    op.drop_table("coach_clients")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
