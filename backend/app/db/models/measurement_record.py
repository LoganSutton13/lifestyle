import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, Text, func
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MeasurementRecord(Base):
    __tablename__ = "measurement_records"
    __table_args__ = (
        Index("idx_measurement_records_client_type_recorded", "client_id", "measurement_type_key", "recorded_at"),
        Index("idx_measurement_records_client_recorded", "client_id", "recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    measurement_type_key: Mapped[str] = mapped_column(Text, ForeignKey("measurement_types.key"), nullable=False)
    value_input: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit_key: Mapped[str] = mapped_column(Text, ForeignKey("measurement_units.key"), nullable=False)
    value_base: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="manual")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

