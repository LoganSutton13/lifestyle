from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.measurement_unit import MeasurementUnit
from app.db.models.user import User
from app.db.models.workout_assignment import WorkoutAssignment
from app.db.models.workout_session import WorkoutSession, WorkoutSessionExercise, WorkoutSet
from app.db.models.workout_template import (
    WorkoutTemplateExercise,
    WorkoutTemplateSet,
    WorkoutTemplateVersion,
)


class WorkoutRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -- Sessions -----------------------------------------------------

    async def get_active_session(self, client_id: UUID) -> WorkoutSession | None:
        result = await self.db.execute(
            select(WorkoutSession).where(
                WorkoutSession.client_id == client_id,
                WorkoutSession.status == "in_progress",
            )
        )
        return result.scalar_one_or_none()

    async def get_session_by_id(self, session_id: UUID) -> WorkoutSession | None:
        result = await self.db.execute(select(WorkoutSession).where(WorkoutSession.id == session_id))
        return result.scalar_one_or_none()

    async def get_session_for_client(self, session_id: UUID, client_id: UUID) -> WorkoutSession | None:
        result = await self.db.execute(
            select(WorkoutSession).where(WorkoutSession.id == session_id, WorkoutSession.client_id == client_id)
        )
        return result.scalar_one_or_none()

    async def lock_session_for_client(self, session_id: UUID, client_id: UUID) -> WorkoutSession | None:
        result = await self.db.execute(
            select(WorkoutSession)
            .where(WorkoutSession.id == session_id, WorkoutSession.client_id == client_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_session_by_assignment(self, assignment_id: UUID) -> WorkoutSession | None:
        result = await self.db.execute(
            select(WorkoutSession).where(WorkoutSession.assignment_id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def add_session(self, session: WorkoutSession) -> WorkoutSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def delete_session_cascade(self, session: WorkoutSession) -> None:
        exercise_ids_result = await self.db.execute(
            select(WorkoutSessionExercise.id).where(WorkoutSessionExercise.session_id == session.id)
        )
        exercise_ids = list(exercise_ids_result.scalars().all())
        if exercise_ids:
            await self.db.execute(
                WorkoutSet.__table__.delete().where(WorkoutSet.session_exercise_id.in_(exercise_ids))
            )
            await self.db.execute(
                WorkoutSessionExercise.__table__.delete().where(WorkoutSessionExercise.session_id == session.id)
            )
        await self.db.delete(session)

    # -- Session exercises ---------------------------------------------

    async def list_session_exercises(self, session_id: UUID) -> list[WorkoutSessionExercise]:
        result = await self.db.execute(
            select(WorkoutSessionExercise)
            .where(WorkoutSessionExercise.session_id == session_id)
            .order_by(WorkoutSessionExercise.position.asc())
        )
        return list(result.scalars().all())

    async def get_session_exercise(
        self, session_exercise_id: UUID, session_id: UUID
    ) -> WorkoutSessionExercise | None:
        result = await self.db.execute(
            select(WorkoutSessionExercise).where(
                WorkoutSessionExercise.id == session_exercise_id,
                WorkoutSessionExercise.session_id == session_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_exercises(self, session_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(WorkoutSessionExercise)
            .where(WorkoutSessionExercise.session_id == session_id)
        )
        return result.scalar_one()

    async def next_exercise_position(self, session_id: UUID) -> int:
        result = await self.db.execute(
            select(func.max(WorkoutSessionExercise.position)).where(
                WorkoutSessionExercise.session_id == session_id
            )
        )
        current_max = result.scalar_one()
        return 0 if current_max is None else current_max + 1

    async def add_session_exercise(self, row: WorkoutSessionExercise) -> WorkoutSessionExercise:
        self.db.add(row)
        await self.db.flush()
        return row

    async def delete_session_exercise_cascade(self, row: WorkoutSessionExercise) -> None:
        await self.db.execute(WorkoutSet.__table__.delete().where(WorkoutSet.session_exercise_id == row.id))
        await self.db.delete(row)

    async def reorder_session_exercises(self, session_id: UUID, ordered_ids: list[UUID]) -> None:
        rows = await self.list_session_exercises(session_id)
        by_id = {row.id: row for row in rows}
        # Two-pass update avoids colliding with the (session_id, position) unique constraint.
        offset = len(ordered_ids) + 1000
        for index, exercise_id in enumerate(ordered_ids):
            by_id[exercise_id].position = offset + index
        await self.db.flush()
        for index, exercise_id in enumerate(ordered_ids):
            by_id[exercise_id].position = index
        await self.db.flush()

    # -- Sets -------------------------------------------------------------

    async def list_sets(self, session_exercise_id: UUID) -> list[WorkoutSet]:
        result = await self.db.execute(
            select(WorkoutSet)
            .where(WorkoutSet.session_exercise_id == session_exercise_id)
            .order_by(WorkoutSet.position.asc())
        )
        return list(result.scalars().all())

    async def list_sets_for_session(self, session_id: UUID) -> dict[UUID, list[WorkoutSet]]:
        result = await self.db.execute(
            select(WorkoutSet)
            .join(WorkoutSessionExercise, WorkoutSessionExercise.id == WorkoutSet.session_exercise_id)
            .where(WorkoutSessionExercise.session_id == session_id)
            .order_by(WorkoutSet.session_exercise_id.asc(), WorkoutSet.position.asc())
        )
        mapping: dict[UUID, list[WorkoutSet]] = {}
        for row in result.scalars().all():
            mapping.setdefault(row.session_exercise_id, []).append(row)
        return mapping

    async def get_set(self, set_id: UUID, session_exercise_id: UUID) -> WorkoutSet | None:
        result = await self.db.execute(
            select(WorkoutSet).where(
                WorkoutSet.id == set_id, WorkoutSet.session_exercise_id == session_exercise_id
            )
        )
        return result.scalar_one_or_none()

    async def count_sets(self, session_exercise_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(WorkoutSet).where(WorkoutSet.session_exercise_id == session_exercise_id)
        )
        return result.scalar_one()

    async def next_set_position(self, session_exercise_id: UUID) -> int:
        result = await self.db.execute(
            select(func.max(WorkoutSet.position)).where(WorkoutSet.session_exercise_id == session_exercise_id)
        )
        current_max = result.scalar_one()
        return 0 if current_max is None else current_max + 1

    async def add_set(self, row: WorkoutSet) -> WorkoutSet:
        self.db.add(row)
        await self.db.flush()
        return row

    async def delete_set(self, row: WorkoutSet) -> None:
        await self.db.delete(row)

    async def renumber_sets(self, session_exercise_id: UUID) -> None:
        rows = await self.list_sets(session_exercise_id)
        offset = len(rows) + 1000
        for index, row in enumerate(rows):
            row.position = offset + index
        await self.db.flush()
        for index, row in enumerate(rows):
            row.position = index
        await self.db.flush()

    async def delete_incomplete_sets(self, session_id: UUID) -> None:
        exercise_ids_result = await self.db.execute(
            select(WorkoutSessionExercise.id).where(WorkoutSessionExercise.session_id == session_id)
        )
        exercise_ids = list(exercise_ids_result.scalars().all())
        if not exercise_ids:
            return
        await self.db.execute(
            WorkoutSet.__table__.delete().where(
                WorkoutSet.session_exercise_id.in_(exercise_ids), WorkoutSet.completed_at.is_(None)
            )
        )

    async def delete_empty_session_exercises(self, session_id: UUID) -> None:
        remaining_with_sets = await self.db.execute(
            select(WorkoutSet.session_exercise_id)
            .join(WorkoutSessionExercise, WorkoutSessionExercise.id == WorkoutSet.session_exercise_id)
            .where(WorkoutSessionExercise.session_id == session_id)
            .distinct()
        )
        ids_with_sets = set(remaining_with_sets.scalars().all())
        all_exercise_ids = await self.db.execute(
            select(WorkoutSessionExercise.id).where(WorkoutSessionExercise.session_id == session_id)
        )
        empty_ids = [row for row in all_exercise_ids.scalars().all() if row not in ids_with_sets]
        if empty_ids:
            await self.db.execute(
                WorkoutSessionExercise.__table__.delete().where(WorkoutSessionExercise.id.in_(empty_ids))
            )

    async def count_completed_sets(self, session_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(WorkoutSet)
            .join(WorkoutSessionExercise, WorkoutSessionExercise.id == WorkoutSet.session_exercise_id)
            .where(WorkoutSessionExercise.session_id == session_id, WorkoutSet.completed_at.isnot(None))
        )
        return result.scalar_one()

    # -- Units -------------------------------------------------------------

    async def get_weight_unit(self, key: str) -> MeasurementUnit | None:
        result = await self.db.execute(
            select(MeasurementUnit).where(MeasurementUnit.key == key, MeasurementUnit.dimension == "weight")
        )
        return result.scalar_one_or_none()

    # -- Templates / assignments (read side) --------------------------

    async def get_assignment(self, assignment_id: UUID) -> WorkoutAssignment | None:
        result = await self.db.execute(select(WorkoutAssignment).where(WorkoutAssignment.id == assignment_id))
        return result.scalar_one_or_none()

    async def lock_assignment(self, assignment_id: UUID) -> WorkoutAssignment | None:
        result = await self.db.execute(
            select(WorkoutAssignment).where(WorkoutAssignment.id == assignment_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_template_version(self, version_id: UUID) -> WorkoutTemplateVersion | None:
        result = await self.db.execute(
            select(WorkoutTemplateVersion).where(WorkoutTemplateVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def count_template_exercises_map(self, template_version_ids: list[UUID]) -> dict[UUID, int]:
        if not template_version_ids:
            return {}
        result = await self.db.execute(
            select(WorkoutTemplateExercise.template_version_id, func.count(WorkoutTemplateExercise.id))
            .where(WorkoutTemplateExercise.template_version_id.in_(template_version_ids))
            .group_by(WorkoutTemplateExercise.template_version_id)
        )
        return {row[0]: row[1] for row in result.all()}

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

    async def get_template_exercises_map(
        self, template_exercise_ids: list[UUID]
    ) -> dict[UUID, WorkoutTemplateExercise]:
        if not template_exercise_ids:
            return {}
        result = await self.db.execute(
            select(WorkoutTemplateExercise).where(WorkoutTemplateExercise.id.in_(template_exercise_ids))
        )
        return {row.id: row for row in result.scalars().all()}

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

    # -- Suggestions -------------------------------------------------------

    async def recent_exercise_ids_for_client(self, client_id: UUID, limit: int) -> list[UUID]:
        result = await self.db.execute(
            select(WorkoutSessionExercise.exercise_id, func.max(WorkoutSession.started_at).label("last_used"))
            .join(WorkoutSession, WorkoutSession.id == WorkoutSessionExercise.session_id)
            .where(WorkoutSession.client_id == client_id)
            .group_by(WorkoutSessionExercise.exercise_id)
            .order_by(func.max(WorkoutSession.started_at).desc())
            .limit(limit)
        )
        return [row[0] for row in result.all()]

    # -- History -------------------------------------------------------------

    async def list_history(
        self,
        client_id: UUID,
        cursor_started_at: str | None,
        cursor_id: UUID | None,
        limit: int,
    ) -> list[WorkoutSession]:
        stmt = select(WorkoutSession).where(
            WorkoutSession.client_id == client_id, WorkoutSession.status == "completed"
        )
        if cursor_started_at is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    WorkoutSession.started_at < cursor_started_at,
                    and_(WorkoutSession.started_at == cursor_started_at, WorkoutSession.id < cursor_id),
                )
            )
        stmt = stmt.order_by(WorkoutSession.started_at.desc(), WorkoutSession.id.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def session_aggregate_counts(self, session_ids: list[UUID]) -> dict[UUID, tuple[int, int]]:
        """Return {session_id: (exercise_count, completed_set_count)}."""
        if not session_ids:
            return {}
        exercise_counts = await self.db.execute(
            select(WorkoutSessionExercise.session_id, func.count(WorkoutSessionExercise.id))
            .where(WorkoutSessionExercise.session_id.in_(session_ids))
            .group_by(WorkoutSessionExercise.session_id)
        )
        exercise_map = {row[0]: row[1] for row in exercise_counts.all()}
        set_counts = await self.db.execute(
            select(WorkoutSessionExercise.session_id, func.count(WorkoutSet.id))
            .join(WorkoutSet, WorkoutSet.session_exercise_id == WorkoutSessionExercise.id)
            .where(
                WorkoutSessionExercise.session_id.in_(session_ids),
                WorkoutSet.completed_at.isnot(None),
            )
            .group_by(WorkoutSessionExercise.session_id)
        )
        set_map = {row[0]: row[1] for row in set_counts.all()}
        return {sid: (exercise_map.get(sid, 0), set_map.get(sid, 0)) for sid in session_ids}

    # -- Assignments (client-facing list) --------------------------------

    async def list_assignments_for_client(
        self,
        client_id: UUID,
        state: str | None,
        cursor_assigned_at,
        cursor_id: UUID | None,
        limit: int,
    ) -> list[tuple[WorkoutAssignment, WorkoutTemplateVersion, User | None, WorkoutSession | None]]:
        stmt = (
            select(WorkoutAssignment, WorkoutTemplateVersion, User, WorkoutSession)
            .join(WorkoutTemplateVersion, WorkoutTemplateVersion.id == WorkoutAssignment.template_version_id)
            .outerjoin(User, User.id == WorkoutAssignment.assigned_by_user_id)
            .outerjoin(WorkoutSession, WorkoutSession.assignment_id == WorkoutAssignment.id)
            .where(WorkoutAssignment.client_id == client_id)
        )
        if state == "available":
            stmt = stmt.where(WorkoutAssignment.canceled_at.is_(None), WorkoutSession.id.is_(None))
        elif state == "in_progress":
            stmt = stmt.where(WorkoutSession.status == "in_progress")
        elif state == "completed":
            stmt = stmt.where(WorkoutSession.status == "completed")
        else:
            # No explicit filter: hide canceled assignments that never produced a session,
            # but keep canceled assignments whose linked session still exists.
            stmt = stmt.where(or_(WorkoutAssignment.canceled_at.is_(None), WorkoutSession.id.isnot(None)))
        if cursor_assigned_at is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    WorkoutAssignment.assigned_at < cursor_assigned_at,
                    and_(WorkoutAssignment.assigned_at == cursor_assigned_at, WorkoutAssignment.id < cursor_id),
                )
            )
        stmt = stmt.order_by(WorkoutAssignment.assigned_at.desc(), WorkoutAssignment.id.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.all())

    async def get_assignment_with_version(
        self, assignment_id: UUID
    ) -> tuple[WorkoutAssignment, WorkoutTemplateVersion, User | None, WorkoutSession | None] | None:
        result = await self.db.execute(
            select(WorkoutAssignment, WorkoutTemplateVersion, User, WorkoutSession)
            .join(WorkoutTemplateVersion, WorkoutTemplateVersion.id == WorkoutAssignment.template_version_id)
            .outerjoin(User, User.id == WorkoutAssignment.assigned_by_user_id)
            .outerjoin(WorkoutSession, WorkoutSession.assignment_id == WorkoutAssignment.id)
            .where(WorkoutAssignment.id == assignment_id)
        )
        return result.first()
