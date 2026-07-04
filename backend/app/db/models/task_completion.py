import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, func
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskCompletion(Base):
    __tablename__ = "task_completions"
    __table_args__ = (Index("idx_task_completions_client_date", "client_id", "completion_date"),)

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assigned_tasks.id", ondelete="CASCADE"), primary_key=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    completion_date: Mapped[date] = mapped_column(Date, primary_key=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

