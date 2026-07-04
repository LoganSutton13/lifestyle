from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import ForbiddenError, NotFoundError, ValidationError
from app.db.models.assigned_task import AssignedTask
from app.repositories.checklist import ChecklistRepository
from app.schemas.checklist import (
    ChecklistHistoryResponse,
    ChecklistResponse,
    ChecklistTask,
    DailyNoteInfo,
    DailyNoteRequest,
    DailyNotesListResponse,
    DailyNotesListItem,
    ChecklistHistoryDay,
    TaskCompletionRequest,
)
from app.schemas.coach import CoachTaskItem, CoachTaskListResponse, TaskCreateRequest, TaskUpdateRequest

MAX_RANGE_DAYS = 1095


class ChecklistService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.checklist = ChecklistRepository(db)

    async def get_checklist(self, client_id: UUID, target_date: date) -> ChecklistResponse:
        tasks = await self.checklist.list_active_tasks_for_date(client_id, target_date)
        completions = await self.checklist.completions_for_date(client_id, target_date)
        completed_ids = {c.task_id for c in completions}
        note = await self.checklist.get_daily_note(client_id, target_date)
        return ChecklistResponse(
            date=target_date,
            tasks=[
                ChecklistTask(
                    id=t.id,
                    title=t.title,
                    description=t.description,
                    completed=t.id in completed_ids,
                )
                for t in tasks
            ],
            note=DailyNoteInfo(body=note.body if note else "", updatedAt=note.updated_at if note else None),
        )

    async def set_completion(
        self, client_id: UUID, task_id: UUID, data: TaskCompletionRequest
    ) -> None:
        task = await self.checklist.get_task(task_id)
        if not task or task.client_id != client_id:
            raise NotFoundError("Task not found")
        await self.checklist.set_completion(task_id, client_id, data.date, data.completed)
        await self.db.commit()

    async def save_daily_note(self, client_id: UUID, data: DailyNoteRequest) -> DailyNoteInfo:
        note = await self.checklist.upsert_daily_note(client_id, data.date, data.body)
        await self.db.commit()
        await self.db.refresh(note)
        return DailyNoteInfo(body=note.body, updatedAt=note.updated_at)

    async def list_coach_tasks(
        self, coach_id: UUID, client_id: UUID, active_only: bool
    ) -> CoachTaskListResponse:
        tasks = await self.checklist.list_tasks_for_coach(coach_id, client_id, active_only)
        return CoachTaskListResponse(
            items=[
                CoachTaskItem(
                    id=t.id,
                    title=t.title,
                    description=t.description,
                    activeFrom=t.active_from,
                    activeUntil=t.active_until,
                    repeatsDaily=t.repeats_daily,
                    archivedAt=t.archived_at,
                )
                for t in tasks
            ]
        )

    async def create_task(self, coach_id: UUID, client_id: UUID, data: TaskCreateRequest) -> CoachTaskItem:
        if data.active_until and data.active_until < data.active_from:
            raise ValidationError("activeUntil must be on or after activeFrom")
        task = AssignedTask(
            coach_id=coach_id,
            client_id=client_id,
            title=data.title,
            description=data.description,
            active_from=data.active_from,
            active_until=data.active_until,
            repeats_daily=data.repeats_daily,
        )
        await self.checklist.add_task(task)
        await self.db.commit()
        await self.db.refresh(task)
        return CoachTaskItem(
            id=task.id,
            title=task.title,
            description=task.description,
            activeFrom=task.active_from,
            activeUntil=task.active_until,
            repeatsDaily=task.repeats_daily,
            archivedAt=task.archived_at,
        )

    async def update_task(
        self, coach_id: UUID, client_id: UUID, task_id: UUID, data: TaskUpdateRequest
    ) -> CoachTaskItem:
        task = await self.checklist.get_task(task_id)
        if not task or task.coach_id != coach_id or task.client_id != client_id:
            raise NotFoundError("Task not found")
        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.active_from is not None:
            task.active_from = data.active_from
        if data.active_until is not None:
            task.active_until = data.active_until
        if data.repeats_daily is not None:
            task.repeats_daily = data.repeats_daily
        if task.active_until and task.active_until < task.active_from:
            raise ValidationError("activeUntil must be on or after activeFrom")
        await self.db.commit()
        await self.db.refresh(task)
        return CoachTaskItem(
            id=task.id,
            title=task.title,
            description=task.description,
            activeFrom=task.active_from,
            activeUntil=task.active_until,
            repeatsDaily=task.repeats_daily,
            archivedAt=task.archived_at,
        )

    async def delete_task(self, coach_id: UUID, client_id: UUID, task_id: UUID) -> None:
        task = await self.checklist.get_task(task_id)
        if not task or task.coach_id != coach_id or task.client_id != client_id:
            raise NotFoundError("Task not found")
        await self.checklist.delete_task(task)
        await self.db.commit()

    def _validate_history_range(self, start: date, end: date) -> None:
        if (end - start).days > MAX_RANGE_DAYS:
            raise ValidationError("Date range cannot exceed 3 years")

    async def checklist_history(
        self, client_id: UUID, start_date: date, end_date: date
    ) -> ChecklistHistoryResponse:
        self._validate_history_range(start_date, end_date)
        history = await self.checklist.checklist_history(client_id, start_date, end_date)
        return ChecklistHistoryResponse(
            items=[
                ChecklistHistoryDay(date=d, totalTasks=total, completedTasks=completed)
                for d, total, completed in history
            ]
        )

    async def list_daily_notes(
        self, client_id: UUID, start_date: date, end_date: date
    ) -> DailyNotesListResponse:
        self._validate_history_range(start_date, end_date)
        notes = await self.checklist.list_daily_notes(client_id, start_date, end_date)
        return DailyNotesListResponse(
            items=[
                DailyNotesListItem(date=n.note_date, body=n.body, updatedAt=n.updated_at) for n in notes
            ]
        )
