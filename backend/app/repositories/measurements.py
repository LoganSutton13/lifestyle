from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.measurement_record import MeasurementRecord
from app.db.models.measurement_type import MeasurementType
from app.db.models.measurement_unit import MeasurementUnit


class MeasurementRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_active_types(self) -> list[MeasurementType]:
        result = await self.db.execute(
            select(MeasurementType).where(MeasurementType.active.is_(True)).order_by(MeasurementType.sort_order)
        )
        return list(result.scalars().all())

    async def get_type(self, key: str) -> MeasurementType | None:
        result = await self.db.execute(
            select(MeasurementType).where(MeasurementType.key == key, MeasurementType.active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_unit(self, key: str) -> MeasurementUnit | None:
        result = await self.db.execute(select(MeasurementUnit).where(MeasurementUnit.key == key))
        return result.scalar_one_or_none()

    async def add_record(self, record: MeasurementRecord) -> MeasurementRecord:
        self.db.add(record)
        await self.db.flush()
        return record

    async def list_records(
        self, client_id: UUID, type_key: str, start: datetime, end: datetime
    ) -> list[MeasurementRecord]:
        result = await self.db.execute(
            select(MeasurementRecord)
            .where(
                MeasurementRecord.client_id == client_id,
                MeasurementRecord.measurement_type_key == type_key,
                MeasurementRecord.recorded_at >= start,
                MeasurementRecord.recorded_at <= end,
            )
            .order_by(MeasurementRecord.recorded_at.asc())
        )
        return list(result.scalars().all())

    async def latest_body_weight(self, client_id: UUID) -> MeasurementRecord | None:
        result = await self.db.execute(
            select(MeasurementRecord)
            .where(
                MeasurementRecord.client_id == client_id,
                MeasurementRecord.measurement_type_key == "body_weight",
            )
            .order_by(MeasurementRecord.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
