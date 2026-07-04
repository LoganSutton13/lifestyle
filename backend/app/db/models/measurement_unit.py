from decimal import Decimal

from sqlalchemy import Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MeasurementUnit(Base):
    __tablename__ = "measurement_units"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    dimension: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    system: Mapped[str] = mapped_column(Text, nullable=False)
    to_base_multiplier: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False, default=1)
    to_base_offset: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False, default=0)

