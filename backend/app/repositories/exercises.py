from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.exercise import Exercise, ExerciseMuscleGroup
from app.db.models.exercise_equipment import ExerciseEquipment
from app.db.models.muscle_group import MuscleGroup
from app.db.models.workout_session import WorkoutSessionExercise
from app.db.models.workout_template import WorkoutTemplateExercise


class ExerciseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        result = await self.db.execute(select(Exercise).where(Exercise.id == exercise_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Exercise | None:
        result = await self.db.execute(select(Exercise).where(Exercise.slug == slug))
        return result.scalar_one_or_none()

    async def find_duplicate(
        self, normalized_name: str, equipment_key: str, exclude_id: UUID | None = None
    ) -> Exercise | None:
        query = select(Exercise).where(
            Exercise.normalized_name == normalized_name,
            Exercise.equipment_key == equipment_key,
        )
        if exclude_id is not None:
            query = query.where(Exercise.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_equipment(self, key: str) -> ExerciseEquipment | None:
        result = await self.db.execute(
            select(ExerciseEquipment).where(ExerciseEquipment.key == key, ExerciseEquipment.active.is_(True))
        )
        return result.scalar_one_or_none()

    async def list_equipment_map(self) -> dict[str, ExerciseEquipment]:
        result = await self.db.execute(select(ExerciseEquipment))
        return {row.key: row for row in result.scalars().all()}

    async def get_muscle_group(self, key: str) -> MuscleGroup | None:
        result = await self.db.execute(
            select(MuscleGroup).where(MuscleGroup.key == key, MuscleGroup.active.is_(True))
        )
        return result.scalar_one_or_none()

    async def list_muscle_groups_map(self) -> dict[str, MuscleGroup]:
        result = await self.db.execute(select(MuscleGroup))
        return {row.key: row for row in result.scalars().all()}

    async def muscle_groups_exist(self, keys: list[str]) -> bool:
        if not keys:
            return True
        result = await self.db.execute(
            select(MuscleGroup.key).where(MuscleGroup.key.in_(keys), MuscleGroup.active.is_(True))
        )
        found = {row for row in result.scalars().all()}
        return found == set(keys)

    async def get_muscle_groups_for_exercises(
        self, exercise_ids: list[UUID]
    ) -> dict[UUID, list[ExerciseMuscleGroup]]:
        if not exercise_ids:
            return {}
        result = await self.db.execute(
            select(ExerciseMuscleGroup)
            .where(ExerciseMuscleGroup.exercise_id.in_(exercise_ids))
            .order_by(ExerciseMuscleGroup.sort_order)
        )
        mapping: dict[UUID, list[ExerciseMuscleGroup]] = {}
        for row in result.scalars().all():
            mapping.setdefault(row.exercise_id, []).append(row)
        return mapping

    async def replace_muscle_groups(
        self, exercise_id: UUID, primary_keys: list[str], secondary_keys: list[str]
    ) -> None:
        await self.db.execute(
            ExerciseMuscleGroup.__table__.delete().where(ExerciseMuscleGroup.exercise_id == exercise_id)
        )
        rows = [
            ExerciseMuscleGroup(exercise_id=exercise_id, muscle_group_key=key, role="primary", sort_order=i)
            for i, key in enumerate(primary_keys)
        ] + [
            ExerciseMuscleGroup(exercise_id=exercise_id, muscle_group_key=key, role="secondary", sort_order=i)
            for i, key in enumerate(secondary_keys)
        ]
        for row in rows:
            self.db.add(row)
        await self.db.flush()

    async def add(self, exercise: Exercise) -> Exercise:
        self.db.add(exercise)
        await self.db.flush()
        return exercise

    async def is_referenced(self, exercise_id: UUID) -> bool:
        session_ref = await self.db.execute(
            select(WorkoutSessionExercise.id).where(WorkoutSessionExercise.exercise_id == exercise_id).limit(1)
        )
        if session_ref.scalar_one_or_none() is not None:
            return True
        template_ref = await self.db.execute(
            select(WorkoutTemplateExercise.id).where(WorkoutTemplateExercise.exercise_id == exercise_id).limit(1)
        )
        return template_ref.scalar_one_or_none() is not None

    async def search(
        self,
        query: str | None,
        equipment_key: str | None,
        muscle_group_key: str | None,
        include_archived: bool,
        cursor_name: str | None,
        cursor_id: UUID | None,
        limit: int,
    ) -> list[Exercise]:
        stmt = select(Exercise)
        if not include_archived:
            stmt = stmt.where(Exercise.archived_at.is_(None))
        if query:
            pattern = f"%{query.strip().lower()}%"
            stmt = stmt.where(Exercise.normalized_name.like(pattern))
        if equipment_key:
            stmt = stmt.where(Exercise.equipment_key == equipment_key)
        if muscle_group_key:
            stmt = stmt.where(
                Exercise.id.in_(
                    select(ExerciseMuscleGroup.exercise_id).where(
                        ExerciseMuscleGroup.muscle_group_key == muscle_group_key
                    )
                )
            )
        if cursor_name is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    Exercise.normalized_name > cursor_name,
                    and_(Exercise.normalized_name == cursor_name, Exercise.id > cursor_id),
                )
            )
        stmt = stmt.order_by(Exercise.normalized_name.asc(), Exercise.id.asc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_alpha_active(self, exclude_ids: set[UUID], limit: int) -> list[Exercise]:
        if limit <= 0:
            return []
        stmt = select(Exercise).where(Exercise.archived_at.is_(None))
        if exclude_ids:
            stmt = stmt.where(Exercise.id.notin_(exclude_ids))
        stmt = stmt.order_by(Exercise.normalized_name.asc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_ids(self, exercise_ids: list[UUID]) -> dict[UUID, Exercise]:
        if not exercise_ids:
            return {}
        result = await self.db.execute(select(Exercise).where(Exercise.id.in_(exercise_ids)))
        return {row.id: row for row in result.scalars().all()}
