"""Seed reference data for meal categories, measurement units, types, and the workout catalog."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.exercise import Exercise, ExerciseMuscleGroup
from app.db.models.exercise_equipment import ExerciseEquipment
from app.db.models.meal_category import MealCategory
from app.db.models.measurement_type import MeasurementType
from app.db.models.measurement_unit import MeasurementUnit
from app.db.models.muscle_group import MuscleGroup
from app.db.session import AsyncSessionLocal
from app.services.text_utils import normalize_name, slugify


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

    await seed_workout_catalog(session)


EQUIPMENT = [
    ("barbell", "Barbell", 10),
    ("dumbbell", "Dumbbell", 20),
    ("machine", "Machine", 30),
    ("cable", "Cable", 40),
    ("bodyweight", "Bodyweight", 50),
    ("kettlebell", "Kettlebell", 60),
    ("band", "Band", 70),
    ("other", "Other", 80),
]

MUSCLE_GROUPS = [
    ("chest", "Chest", 10),
    ("back", "Back", 20),
    ("shoulders", "Shoulders", 30),
    ("biceps", "Biceps", 40),
    ("triceps", "Triceps", 50),
    ("forearms", "Forearms", 60),
    ("quadriceps", "Quadriceps", 70),
    ("hamstrings", "Hamstrings", 80),
    ("glutes", "Glutes", 90),
    ("calves", "Calves", 100),
    ("core", "Core", 110),
    ("full_body", "Full Body", 120),
]

# (name, equipment_key, tracking_type, default_rest_seconds, default_unilateral, primary_muscles, secondary_muscles)
STARTER_EXERCISES: list[tuple[str, str, str, int, bool, list[str], list[str]]] = [
    ("Barbell Bench Press", "barbell", "reps_load", 120, False, ["chest"], ["triceps", "shoulders"]),
    ("Barbell Back Squat", "barbell", "reps_load", 150, False, ["quadriceps"], ["glutes", "hamstrings"]),
    ("Conventional Deadlift", "barbell", "reps_load", 180, False, ["back"], ["hamstrings", "glutes"]),
    ("Overhead Press", "barbell", "reps_load", 120, False, ["shoulders"], ["triceps"]),
    ("Barbell Row", "barbell", "reps_load", 120, False, ["back"], ["biceps"]),
    ("Pull-Up", "bodyweight", "reps_only", 90, False, ["back"], ["biceps"]),
    ("Lat Pulldown", "cable", "reps_load", 90, False, ["back"], ["biceps"]),
    ("Dumbbell Curl", "dumbbell", "reps_load", 60, False, ["biceps"], ["forearms"]),
    ("Triceps Pushdown", "cable", "reps_load", 60, False, ["triceps"], []),
    ("Leg Press", "machine", "reps_load", 120, False, ["quadriceps"], ["glutes", "hamstrings"]),
    ("Romanian Deadlift", "barbell", "reps_load", 120, False, ["hamstrings"], ["glutes"]),
    ("Plank", "bodyweight", "duration", 60, False, ["core"], []),
    ("Dumbbell Shoulder Press", "dumbbell", "reps_load", 90, False, ["shoulders"], ["triceps"]),
    ("Seated Cable Row", "cable", "reps_load", 90, False, ["back"], ["biceps"]),
    ("Leg Curl", "machine", "reps_load", 90, False, ["hamstrings"], []),
    ("Leg Extension", "machine", "reps_load", 90, False, ["quadriceps"], []),
    ("Dumbbell Lateral Raise", "dumbbell", "reps_load", 60, False, ["shoulders"], []),
    ("Standing Calf Raise", "machine", "reps_load", 60, False, ["calves"], []),
    ("Kettlebell Swing", "kettlebell", "reps_only", 90, False, ["glutes"], ["hamstrings", "core"]),
    ("Farmer's Carry", "kettlebell", "duration", 90, False, ["forearms"], ["core"]),
]


async def seed_workout_catalog(session: AsyncSession) -> None:
    for key, display_name, sort_order in EQUIPMENT:
        existing = await session.get(ExerciseEquipment, key)
        if not existing:
            session.add(ExerciseEquipment(key=key, display_name=display_name, sort_order=sort_order))
    for key, display_name, sort_order in MUSCLE_GROUPS:
        existing = await session.get(MuscleGroup, key)
        if not existing:
            session.add(MuscleGroup(key=key, display_name=display_name, sort_order=sort_order))
    await session.commit()

    for name, equipment_key, tracking_type, rest_seconds, unilateral, primary, secondary in STARTER_EXERCISES:
        slug = slugify(name)
        existing_result = await session.execute(select(Exercise).where(Exercise.slug == slug))
        if existing_result.scalar_one_or_none():
            continue
        exercise = Exercise(
            slug=slug,
            name=name,
            normalized_name=normalize_name(name),
            equipment_key=equipment_key,
            tracking_type=tracking_type,
            default_unilateral=unilateral,
            default_rest_seconds=rest_seconds,
            instructions="",
            created_by_user_id=None,
        )
        session.add(exercise)
        await session.flush()
        for sort_order, muscle_key in enumerate(primary):
            session.add(
                ExerciseMuscleGroup(
                    exercise_id=exercise.id, muscle_group_key=muscle_key, role="primary", sort_order=sort_order
                )
            )
        for sort_order, muscle_key in enumerate(secondary):
            session.add(
                ExerciseMuscleGroup(
                    exercise_id=exercise.id, muscle_group_key=muscle_key, role="secondary", sort_order=sort_order
                )
            )
    await session.commit()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_reference_data(session)
    print("Reference data seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
