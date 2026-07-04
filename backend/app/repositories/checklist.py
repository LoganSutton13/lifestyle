from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assigned_task import AssignedTask
from app.db.models.daily_note import DailyNote
from app.db.models.task_completion import TaskCompletion


class ChecklistRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_task(self, task_id: UUID) -> AssignedTask | None:
        result = await self.db.execute(select(AssignedTask).where(AssignedTask.id == task_id))
        return result.scalar_one_or_none()

    async def list_active_tasks_for_date(self, client_id: UUID, target_date: date) -> list[AssignedTask]:
        result = await self.db.execute(
            select(AssignedTask)
            .where(
                AssignedTask.client_id == client_id,
                AssignedTask.archived_at.is_(None),
                AssignedTask.active_from <= target_date,
                or_(AssignedTask.active_until.is_(None), AssignedTask.active_until >= target_date),
            )
            .order_by(AssignedTask.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_tasks_for_coach(
        self, coach_id: UUID, client_id: UUID, active_only: bool = True
    ) -> list[AssignedTask]:
        query = select(AssignedTask).where(
            AssignedTask.coach_id == coach_id,
            AssignedTask.client_id == client_id,
        )
        if active_only:
            query = query.where(AssignedTask.archived_at.is_(None))
        result = await self.db.execute(query.order_by(AssignedTask.created_at.desc()))
        return list(result.scalars().all())

    async def add_task(self, task: AssignedTask) -> AssignedTask:
        self.db.add(task)
        await self.db.flush()
        return task

    async def delete_task(self, task: AssignedTask) -> None:
        await self.db.delete(task)

    async def get_completion(self, task_id: UUID, completion_date: date) -> TaskCompletion | None:
        result = await self.db.execute(
            select(TaskCompletion).where(
                TaskCompletion.task_id == task_id,
                TaskCompletion.completion_date == completion_date,
            )
        )
        return result.scalar_one_or_none()

    async def set_completion(self, task_id: UUID, client_id: UUID, completion_date: date, completed: bool) -> None:
        existing = await self.get_completion(task_id, completion_date)
        if completed:
            if not existing:
                self.db.add(
                    TaskCompletion(task_id=task_id, client_id=client_id, completion_date=completion_date)
                )
        elif existing:
            await self.db.delete(existing)

    async def completions_for_date(self, client_id: UUID, target_date: date) -> list[TaskCompletion]:
        result = await self.db.execute(
            select(TaskCompletion).where(
                TaskCompletion.client_id == client_id,
                TaskCompletion.completion_date == target_date,
            )
        )
        return list(result.scalars().all())

    async def get_daily_note(self, client_id: UUID, note_date: date) -> DailyNote | None:
        result = await self.db.execute(
            select(DailyNote).where(DailyNote.client_id == client_id, DailyNote.note_date == note_date)
        )
        return result.scalar_one_or_none()

    async def upsert_daily_note(self, client_id: UUID, note_date: date, body: str) -> DailyNote:
        note = await self.get_daily_note(client_id, note_date)
        if note:
            note.body = body
        else:
            note = DailyNote(client_id=client_id, note_date=note_date, body=body)
            self.db.add(note)
        await self.db.flush()
        return note

    async def list_daily_notes(self, client_id: UUID, start_date: date, end_date: date) -> list[DailyNote]:
        result = await self.db.execute(
            select(DailyNote)
            .where(
                DailyNote.client_id == client_id,
                DailyNote.note_date >= start_date,
                DailyNote.note_date <= end_date,
            )
            .order_by(DailyNote.note_date.desc())
        )
        return list(result.scalars().all())

    async def checklist_history(
        self, client_id: UUID, start_date: date, end_date: date
    ) -> list[tuple[date, int, int]]:
        tasks_result = await self.db.execute(
            select(AssignedTask).where(
                AssignedTask.client_id == client_id,
                AssignedTask.active_from <= end_date,
                or_(AssignedTask.active_until.is_(None), AssignedTask.active_until >= start_date),
            )
        )
        tasks = list(tasks_result.scalars().all())
        history: list[tuple[date, int, int]] = []
        current = start_date
        while current <= end_date:
            active_tasks = [
                t
                for t in tasks
                if t.active_from <= current and (t.active_until is None or t.active_until >= current)
            ]
            if active_tasks:
                completions = await self.completions_for_date(client_id, current)
                completed_ids = {c.task_id for c in completions}
                total = len(active_tasks)
                completed = sum(1 for t in active_tasks if t.id in completed_ids)
                history.append((current, total, completed))
            current = date.fromordinal(current.toordinal() + 1)
        return history

    async def count_today_completion(self, client_id: UUID, target_date: date) -> tuple[int, int]:
        tasks = await self.list_active_tasks_for_date(client_id, target_date)
        if not tasks:
            return 0, 0
        completions = await self.completions_for_date(client_id, target_date)
        completed_ids = {c.task_id for c in completions}
        total = len(tasks)
        completed = sum(1 for t in tasks if t.id in completed_ids)
        return completed, total
