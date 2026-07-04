"""Seed reference data for meal categories, measurement units, and types."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.meal_category import MealCategory
from app.db.models.measurement_type import MeasurementType
from app.db.models.measurement_unit import MeasurementUnit
from app.db.session import AsyncSessionLocal


async def seed_reference_data(session: AsyncSession) -> None:
    categories = [
        MealCategory(key="breakfast", display_name="Breakfast", sort_order=10),
        MealCategory(key="lunch", display_name="Lunch", sort_order=20),
        MealCategory(key="dinner", display_name="Dinner", sort_order=30),
        MealCategory(key="dessert", display_name="Dessert", sort_order=40),
    ]
    units = [
        MeasurementUnit(key="kg", dimension="weight", display_name="Kilograms", symbol="kg", system="metric", to_base_multiplier=1),
        MeasurementUnit(key="lb", dimension="weight", display_name="Pounds", symbol="lbs", system="imperial", to_base_multiplier="0.45359237"),
        MeasurementUnit(key="cm", dimension="length", display_name="Centimeters", symbol="cm", system="metric", to_base_multiplier=1),
        MeasurementUnit(key="in", dimension="length", display_name="Inches", symbol="in", system="imperial", to_base_multiplier="2.54"),
        MeasurementUnit(key="count", dimension="count", display_name="Count", symbol="", system="none", to_base_multiplier=1),
    ]
    types = [
        MeasurementType(key="body_weight", display_name="Body Weight", dimension="weight", default_unit_key="lb", sort_order=10),
        MeasurementType(key="waist", display_name="Waist", dimension="length", default_unit_key="in", sort_order=20),
        MeasurementType(key="hips", display_name="Hips", dimension="length", default_unit_key="in", sort_order=30),
        MeasurementType(key="thigh", display_name="Thigh", dimension="length", default_unit_key="in", sort_order=40),
    ]

    for category in categories:
        existing = await session.get(MealCategory, category.key)
        if not existing:
            session.add(category)
    for unit in units:
        existing = await session.get(MeasurementUnit, unit.key)
        if not existing:
            session.add(unit)
    for mtype in types:
        existing = await session.get(MeasurementType, mtype.key)
        if not existing:
            session.add(mtype)
    await session.commit()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_reference_data(session)
    print("Reference data seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
