from datetime import UTC, date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import NotFoundError, ValidationError
from app.core.timezone import date_range_to_utc_bounds, default_date_range
from app.db.models.measurement_record import MeasurementRecord
from app.repositories.measurements import MeasurementRepository
from app.schemas.measurements import (
    MeasurementCreateRequest,
    MeasurementGraphResponse,
    MeasurementPoint,
    MeasurementTypeResponse,
    MeasurementTypesListResponse,
    MeasurementUnitInfo,
)
from app.services.unit_conversion import from_base_value, to_base_value

MAX_RANGE_DAYS = 1095


class MeasurementService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.measurements = MeasurementRepository(db)

    async def list_types(self) -> MeasurementTypesListResponse:
        types = await self.measurements.list_active_types()
        return MeasurementTypesListResponse(
            items=[MeasurementTypeResponse(key=t.key, displayName=t.display_name) for t in types]
        )

    def _default_date_range(self, timezone: str) -> tuple[date, date]:
        return default_date_range(timezone, days=30)

    def _validate_range(self, start: date, end: date) -> None:
        if (end - start).days > MAX_RANGE_DAYS:
            raise ValidationError("Date range cannot exceed 3 years")

    async def get_graph(
        self,
        client_id: UUID,
        type_key: str,
        start_date: date | None,
        end_date: date | None,
        unit_key: str | None,
        timezone: str,
    ) -> MeasurementGraphResponse:
        mtype = await self.measurements.get_type(type_key)
        if not mtype:
            raise NotFoundError("Measurement type not found")
        start, end = start_date, end_date
        if not start or not end:
            start, end = self._default_date_range(timezone)
        self._validate_range(start, end)
        unit_key = unit_key or mtype.default_unit_key
        unit = await self.measurements.get_unit(unit_key)
        if not unit:
            raise ValidationError("Invalid unit")
        start_dt, end_dt = date_range_to_utc_bounds(start, end, timezone)
        records = await self.measurements.list_records(client_id, type_key, start_dt, end_dt)
        points = [
            MeasurementPoint(
                id=r.id,
                recordedAt=r.recorded_at,
                value=from_base_value(r.value_base, unit).quantize(Decimal("0.1")),
            )
            for r in records
        ]
        return MeasurementGraphResponse(
            type=MeasurementTypeResponse(key=mtype.key, displayName=mtype.display_name),
            unit=MeasurementUnitInfo(key=unit.key, symbol=unit.symbol),
            startDate=start,
            endDate=end,
            points=points,
        )

    async def create_record(self, client_id: UUID, data: MeasurementCreateRequest) -> MeasurementPoint:
        mtype = await self.measurements.get_type(data.type_key)
        if not mtype:
            raise NotFoundError("Measurement type not found")
        unit = await self.measurements.get_unit(data.unit_key)
        if not unit:
            raise ValidationError("Invalid unit")
        if unit.dimension != mtype.dimension:
            raise ValidationError("Unit does not match measurement type dimension")
        value_base = to_base_value(data.value, unit)
        record = MeasurementRecord(
            client_id=client_id,
            measurement_type_key=data.type_key,
            value_input=data.value,
            unit_key=data.unit_key,
            value_base=value_base,
            source="manual",
            recorded_at=data.recorded_at.astimezone(UTC),
        )
        await self.measurements.add_record(record)
        await self.db.commit()
        await self.db.refresh(record)
        return MeasurementPoint(
            id=record.id,
            recordedAt=record.recorded_at,
            value=data.value,
        )
