"""Add structured task recurrence fields."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_task_recurrence"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assigned_tasks",
        sa.Column("recurrence_frequency", sa.Text(), server_default="daily", nullable=False),
    )
    op.add_column(
        "assigned_tasks",
        sa.Column("recurrence_interval", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "assigned_tasks",
        sa.Column("recurrence_days", sa.JSON(), server_default="[]", nullable=False),
    )
    op.execute(
        """
        UPDATE assigned_tasks
        SET recurrence_frequency = 'daily',
            recurrence_interval = 1,
            recurrence_days = '[]'::json
        """
    )
    op.drop_column("assigned_tasks", "repeats_daily")


def downgrade() -> None:
    op.add_column(
        "assigned_tasks",
        sa.Column("repeats_daily", sa.Boolean(), server_default="true", nullable=False),
    )
    op.execute(
        """
        UPDATE assigned_tasks
        SET repeats_daily = CASE
            WHEN recurrence_frequency = 'daily' THEN true
            ELSE false
        END
        """
    )
    op.drop_column("assigned_tasks", "recurrence_days")
    op.drop_column("assigned_tasks", "recurrence_interval")
    op.drop_column("assigned_tasks", "recurrence_frequency")
