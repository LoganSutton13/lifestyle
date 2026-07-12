from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workout_assignment import WorkoutAssignment
from app.db.models.workout_template import (
    WorkoutTemplate,
    WorkoutTemplateExercise,
    WorkoutTemplateSet,
    WorkoutTemplateVersion,
)


class WorkoutTemplateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -- Templates ----------------------------------------------------

    async def get_template(self, template_id: UUID) -> WorkoutTemplate | None:
        result = await self.db.execute(select(WorkoutTemplate).where(WorkoutTemplate.id == template_id))
        return result.scalar_one_or_none()

    async def list_templates(self, coach_id: UUID, include_archived: bool) -> list[WorkoutTemplate]:
        stmt = select(WorkoutTemplate).where(WorkoutTemplate.coach_id == coach_id)
        if not include_archived:
            stmt = stmt.where(WorkoutTemplate.archived_at.is_(None))
        stmt = stmt.order_by(WorkoutTemplate.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_template(self, template: WorkoutTemplate) -> WorkoutTemplate:
        self.db.add(template)
        await self.db.flush()
        return template

    # -- Versions -------------------------------------------------------

    async def get_version(self, version_id: UUID) -> WorkoutTemplateVersion | None:
        result = await self.db.execute(
            select(WorkoutTemplateVersion).where(WorkoutTemplateVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_draft_version(self, template_id: UUID) -> WorkoutTemplateVersion | None:
        result = await self.db.execute(
            select(WorkoutTemplateVersion).where(
                WorkoutTemplateVersion.template_id == template_id,
                WorkoutTemplateVersion.status == "draft",
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_published_version(self, template_id: UUID) -> WorkoutTemplateVersion | None:
        result = await self.db.execute(
            select(WorkoutTemplateVersion)
            .where(
                WorkoutTemplateVersion.template_id == template_id,
                WorkoutTemplateVersion.status == "published",
            )
            .order_by(WorkoutTemplateVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_versions(self, template_id: UUID) -> list[WorkoutTemplateVersion]:
        result = await self.db.execute(
            select(WorkoutTemplateVersion)
            .where(WorkoutTemplateVersion.template_id == template_id)
            .order_by(WorkoutTemplateVersion.version_number.asc())
        )
        return list(result.scalars().all())

    async def next_version_number(self, template_id: UUID) -> int:
        result = await self.db.execute(
            select(func.max(WorkoutTemplateVersion.version_number)).where(
                WorkoutTemplateVersion.template_id == template_id
            )
        )
        current_max = result.scalar_one()
        return 1 if current_max is None else current_max + 1

    async def add_version(self, version: WorkoutTemplateVersion) -> WorkoutTemplateVersion:
        self.db.add(version)
        await self.db.flush()
        return version

    # -- Template exercises / sets --------------------------------------

    async def list_template_exercises(self, template_version_id: UUID) -> list[WorkoutTemplateExercise]:
        result = await self.db.execute(
            select(WorkoutTemplateExercise)
            .where(WorkoutTemplateExercise.template_version_id == template_version_id)
            .order_by(WorkoutTemplateExercise.position.asc())
        )
        return list(result.scalars().all())

    async def list_template_sets(self, template_exercise_id: UUID) -> list[WorkoutTemplateSet]:
        result = await self.db.execute(
            select(WorkoutTemplateSet)
            .where(WorkoutTemplateSet.template_exercise_id == template_exercise_id)
            .order_by(WorkoutTemplateSet.position.asc())
        )
        return list(result.scalars().all())

    async def get_template_sets_map(
        self, template_exercise_ids: list[UUID]
    ) -> dict[UUID, list[WorkoutTemplateSet]]:
        if not template_exercise_ids:
            return {}
        result = await self.db.execute(
            select(WorkoutTemplateSet)
            .where(WorkoutTemplateSet.template_exercise_id.in_(template_exercise_ids))
            .order_by(WorkoutTemplateSet.template_exercise_id.asc(), WorkoutTemplateSet.position.asc())
        )
        mapping: dict[UUID, list[WorkoutTemplateSet]] = {}
        for row in result.scalars().all():
            mapping.setdefault(row.template_exercise_id, []).append(row)
        return mapping

    async def add_template_exercise(self, row: WorkoutTemplateExercise) -> WorkoutTemplateExercise:
        self.db.add(row)
        await self.db.flush()
        return row

    async def add_template_set(self, row: WorkoutTemplateSet) -> WorkoutTemplateSet:
        self.db.add(row)
        await self.db.flush()
        return row

    async def replace_version_content(self, template_version_id: UUID) -> None:
        exercise_ids_result = await self.db.execute(
            select(WorkoutTemplateExercise.id).where(
                WorkoutTemplateExercise.template_version_id == template_version_id
            )
        )
        exercise_ids = list(exercise_ids_result.scalars().all())
        if exercise_ids:
            await self.db.execute(
                WorkoutTemplateSet.__table__.delete().where(
                    WorkoutTemplateSet.template_exercise_id.in_(exercise_ids)
                )
            )
            await self.db.execute(
                WorkoutTemplateExercise.__table__.delete().where(
                    WorkoutTemplateExercise.template_version_id == template_version_id
                )
            )

    # -- Assignments (coach-side write + read) ---------------------------

    async def add_assignment(self, assignment: WorkoutAssignment) -> WorkoutAssignment:
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def get_assignment(self, assignment_id: UUID) -> WorkoutAssignment | None:
        result = await self.db.execute(select(WorkoutAssignment).where(WorkoutAssignment.id == assignment_id))
        return result.scalar_one_or_none()

    async def get_assignment_owned_by_coach(
        self, assignment_id: UUID, coach_id: UUID
    ) -> WorkoutAssignment | None:
        result = await self.db.execute(
            select(WorkoutAssignment)
            .join(WorkoutTemplateVersion, WorkoutTemplateVersion.id == WorkoutAssignment.template_version_id)
            .join(WorkoutTemplate, WorkoutTemplate.id == WorkoutTemplateVersion.template_id)
            .where(WorkoutAssignment.id == assignment_id, WorkoutTemplate.coach_id == coach_id)
        )
        return result.scalar_one_or_none()

    async def list_assignments_for_coach_client(
        self,
        coach_id: UUID,
        client_id: UUID,
        cursor_assigned_at: str | None,
        cursor_id: UUID | None,
        limit: int,
    ) -> list[WorkoutAssignment]:
        stmt = select(WorkoutAssignment).where(
            WorkoutAssignment.client_id == client_id, WorkoutAssignment.assigned_by_user_id == coach_id
        )
        if cursor_assigned_at is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    WorkoutAssignment.assigned_at < cursor_assigned_at,
                    and_(WorkoutAssignment.assigned_at == cursor_assigned_at, WorkoutAssignment.id < cursor_id),
                )
            )
        stmt = stmt.order_by(WorkoutAssignment.assigned_at.desc(), WorkoutAssignment.id.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def is_version_referenced_by_assignment(self, template_version_id: UUID) -> bool:
        result = await self.db.execute(
            select(WorkoutAssignment.id)
            .where(WorkoutAssignment.template_version_id == template_version_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
