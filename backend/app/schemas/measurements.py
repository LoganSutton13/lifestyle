from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MeasurementTypeResponse(BaseModel):
    key: str
    display_name: str = Field(alias="displayName")

    model_config = {"populate_by_name": True}


class MeasurementTypesListResponse(BaseModel):
    items: list[MeasurementTypeResponse]


class MeasurementCreateRequest(BaseModel):
    type_key: str = Field(alias="typeKey")
    value: Decimal
    unit_key: str = Field(alias="unitKey")
    recorded_at: datetime = Field(alias="recordedAt")

    model_config = {"populate_by_name": True}

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Decimal) -> Decimal:
        if value <= 0:
            msg = "Value must be greater than zero"
            raise ValueError(msg)
        return value


class MeasurementPoint(BaseModel):
    id: UUID
    recorded_at: datetime = Field(alias="recordedAt")
    value: Decimal

    model_config = {"populate_by_name": True}


class MeasurementUnitInfo(BaseModel):
    key: str
    symbol: str


class MeasurementGraphResponse(BaseModel):
    type: MeasurementTypeResponse
    unit: MeasurementUnitInfo
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    points: list[MeasurementPoint]

    model_config = {"populate_by_name": True}
