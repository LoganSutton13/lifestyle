from decimal import Decimal

from app.db.models.measurement_unit import MeasurementUnit


def to_base_value(value: Decimal, unit: MeasurementUnit) -> Decimal:
    return value * unit.to_base_multiplier + unit.to_base_offset


def from_base_value(value_base: Decimal, unit: MeasurementUnit) -> Decimal:
    return (value_base - unit.to_base_offset) / unit.to_base_multiplier
