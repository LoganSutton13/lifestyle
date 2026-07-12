from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import AppException, NotFoundError, ValidationError
from app.core.cursor import decode_cursor, encode_cursor
from app.db.models.user import User
from app.db.models.workout_assignment import WorkoutAssignment
from app.db.models.workout_session import WorkoutSession
from app.db.models.workout_template import (
    WorkoutTemplate,
    WorkoutTemplateExercise,
    WorkoutTemplateSet,
    WorkoutTemplateVersion,
)
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.exercises import ExerciseRepository
from app.repositories.users import UserRepository
from app.repositories.workout_templates import WorkoutTemplateRepository
from app.repositories.workouts import WorkoutRepository
from app.schemas.coach_workouts import (
    AssignmentCreateRequest,
    TemplateCreateRequest,
    TemplateDetailResponse,
    TemplateDraftUpdateRequest,
    TemplateExerciseResponse,
    TemplateListItem,
    TemplateListResponse,
    TemplateSetResponse,
    TemplateVersionResponse,
)
from app.schemas.workouts import AssignmentListItem, AssignmentListResponse, WorkoutHistoryListResponse
from app.services.unit_conversion import to_base_value
from app.services.workout_service import MAX_PAGE_SIZE, WorkoutService


class WorkoutTemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.templates = WorkoutTemplateRepository(db)
        self.workouts = WorkoutRepository(db)
        self.exercise_repo = ExerciseRepository(db)
        self.users = UserRepository(db)
        self.audit_logs = AuditLogRepository(db)

    # -- Ownership helpers --------------------------------------------------

    async def _get_owned_template(self, coach_id: UUID, template_id: UUID) -> WorkoutTemplate:
        template = await self.templates.get_template(template_id)
        if not template or template.coach_id != coach_id:
            raise NotFoundError("Workout template not found")
        return template

    async def _get_owned_version(
        self, coach_id: UUID, version_id: UUID
    ) -> tuple[WorkoutTemplate, WorkoutTemplateVersion]:
        version = await self.templates.get_version(version_id)
        if not version:
            raise NotFoundError("Template version not found")
        template = await self._get_owned_template(coach_id, version.template_id)
        return template, version

    # -- Response building -------------------------------------------------

    @staticmethod
    def _template_set_response(s: WorkoutTemplateSet) -> TemplateSetResponse:
        return TemplateSetResponse(
            id=s.id,
            position=s.position,
            setType=s.set_type,
            targetRepsMin=s.target_reps_min,
            targetRepsMax=s.target_reps_max,
            targetLoadValue=str(s.target_load_value_input) if s.target_load_value_input is not None else None,
            targetLoadUnitKey=s.target_load_unit_key,
            targetDurationSeconds=s.target_duration_seconds,
            targetRpe=str(s.target_rpe) if s.target_rpe is not None else None,
            notes=s.notes,
        )

    async def _build_version_response(self, version: WorkoutTemplateVersion) -> TemplateVersionResponse:
        template_exercises = await self.templates.list_template_exercises(version.id)
        exercises_by_id = await self.exercise_repo.list_by_ids([te.exercise_id for te in template_exercises])
        sets_map = await self.templates.get_template_sets_map([te.id for te in template_exercises])
        exercise_responses = []
        for te in template_exercises:
            exercise = exercises_by_id.get(te.exercise_id)
            sets = sets_map.get(te.id, [])
            exercise_responses.append(
                TemplateExerciseResponse(
                    id=te.id,
                    position=te.position,
                    exerciseId=te.exercise_id,
                    exerciseName=exercise.name if exercise else "Unknown exercise",
                    isUnilateral=te.is_unilateral,
                    restSeconds=te.rest_seconds,
                    notes=te.notes,
                    sets=[self._template_set_response(s) for s in sets],
                )
            )
        return TemplateVersionResponse(
            id=version.id,
            versionNumber=version.version_number,
            title=version.title,
            notes=version.notes,
            status=version.status,
            createdAt=version.created_at,
            publishedAt=version.published_at,
            exercises=exercise_responses,
        )

    # -- Templates -----------------------------------------------------

    async def list_templates(self, coach_id: UUID, include_archived: bool = False) -> TemplateListResponse:
        templates = await self.templates.list_templates(coach_id, include_archived)
        items = []
        for template in templates:
            versions = await self.templates.list_versions(template.id)
            draft = next((v for v in versions if v.status == "draft"), None)
            published = [v for v in versions if v.status == "published"]
            latest_published = max(published, key=lambda v: v.version_number) if published else None
            title = draft.title if draft else (latest_published.title if latest_published else "Untitled")
            items.append(
                TemplateListItem(
                    id=template.id,
                    archivedAt=template.archived_at,
                    updatedAt=template.updated_at,
                    title=title,
                    hasDraft=draft is not None,
                    latestPublishedVersionNumber=latest_published.version_number if latest_published else None,
                )
            )
        return TemplateListResponse(items=items)

    async def get_template(self, coach_id: UUID, template_id: UUID) -> TemplateDetailResponse:
        template = await self._get_owned_template(coach_id, template_id)
        versions = await self.templates.list_versions(template_id)
        version_responses = [await self._build_version_response(v) for v in versions]
        return TemplateDetailResponse(
            id=template.id, coachId=template.coach_id, archivedAt=template.archived_at, versions=version_responses
        )

    async def create_template(self, coach_id: UUID, data: TemplateCreateRequest) -> TemplateDetailResponse:
        template = WorkoutTemplate(coach_id=coach_id)
        await self.templates.add_template(template)
        version = WorkoutTemplateVersion(
            template_id=template.id,
            version_number=1,
            title=data.title,
            notes=data.notes,
            status="draft",
            created_by_user_id=coach_id,
        )
        await self.templates.add_version(version)
        await self.db.commit()
        return await self.get_template(coach_id, template.id)

    async def delete_template(self, coach_id: UUID, template_id: UUID) -> None:
        template = await self._get_owned_template(coach_id, template_id)
        if template.archived_at is None:
            template.archived_at = datetime.now(UTC)
            await self.db.commit()

    async def create_draft(self, coach_id: UUID, template_id: UUID) -> TemplateVersionResponse:
        await self._get_owned_template(coach_id, template_id)
        existing_draft = await self.templates.get_draft_version(template_id)
        if existing_draft:
            return await self._build_version_response(existing_draft)

        latest_published = await self.templates.get_latest_published_version(template_id)
        if not latest_published:
            raise ValidationError("There is no published version to base a new draft on")

        next_number = await self.templates.next_version_number(template_id)
        new_version = WorkoutTemplateVersion(
            template_id=template_id,
            version_number=next_number,
            title=latest_published.title,
            notes=latest_published.notes,
            status="draft",
            created_by_user_id=coach_id,
        )
        await self.templates.add_version(new_version)

        published_exercises = await self.templates.list_template_exercises(latest_published.id)
        sets_map = await self.templates.get_template_sets_map([te.id for te in published_exercises])
        for te in published_exercises:
            new_te = WorkoutTemplateExercise(
                template_version_id=new_version.id,
                exercise_id=te.exercise_id,
                position=te.position,
                is_unilateral=te.is_unilateral,
                rest_seconds=te.rest_seconds,
                notes=te.notes,
            )
            await self.templates.add_template_exercise(new_te)
            for ts in sets_map.get(te.id, []):
                new_ts = WorkoutTemplateSet(
                    template_exercise_id=new_te.id,
                    position=ts.position,
                    set_type=ts.set_type,
                    target_reps_min=ts.target_reps_min,
                    target_reps_max=ts.target_reps_max,
                    target_load_value_input=ts.target_load_value_input,
                    target_load_unit_key=ts.target_load_unit_key,
                    target_load_value_base=ts.target_load_value_base,
                    target_duration_seconds=ts.target_duration_seconds,
                    target_rpe=ts.target_rpe,
                    notes=ts.notes,
                )
                await self.templates.add_template_set(new_ts)

        await self.db.commit()
        await self.db.refresh(new_version)
        return await self._build_version_response(new_version)

    async def update_draft(
        self, coach_id: UUID, version_id: UUID, data: TemplateDraftUpdateRequest
    ) -> TemplateVersionResponse:
        _, version = await self._get_owned_version(coach_id, version_id)
        if version.status != "draft":
            raise AppException("TEMPLATE_VERSION_IMMUTABLE", "Only a draft version can be edited.", 409)

        positions = [exercise.position for exercise in data.exercises]
        if len(positions) != len(set(positions)):
            raise ValidationError("Exercise positions must be unique")

        exercise_ids = [exercise.exercise_id for exercise in data.exercises]
        exercises_by_id = await self.exercise_repo.list_by_ids(exercise_ids)
        for exercise_input in data.exercises:
            exercise = exercises_by_id.get(exercise_input.exercise_id)
            if not exercise:
                raise ValidationError(f"Exercise {exercise_input.exercise_id} not found")
            if exercise.archived_at is not None:
                raise AppException(
                    "EXERCISE_ARCHIVED", f"Exercise '{exercise.name}' is archived and cannot be used.", 400
                )
            set_positions = [s.position for s in exercise_input.sets]
            if len(set_positions) != len(set(set_positions)):
                raise ValidationError("Set positions must be unique within an exercise")
            for set_input in exercise_input.sets:
                if (
                    set_input.target_reps_min is not None
                    and set_input.target_reps_max is not None
                    and set_input.target_reps_max < set_input.target_reps_min
                ):
                    raise ValidationError("targetRepsMax must be greater than or equal to targetRepsMin")
                if set_input.target_load_value is not None and not set_input.target_load_unit_key:
                    raise ValidationError("targetLoadUnitKey is required when targetLoadValue is provided")
                if set_input.target_load_unit_key:
                    unit = await self.workouts.get_weight_unit(set_input.target_load_unit_key)
                    if not unit:
                        raise ValidationError("targetLoadUnitKey must reference a valid weight unit")

        version.title = data.title
        version.notes = data.notes
        await self.templates.replace_version_content(version.id)
        await self.db.flush()

        for exercise_input in sorted(data.exercises, key=lambda e: e.position):
            new_te = WorkoutTemplateExercise(
                template_version_id=version.id,
                exercise_id=exercise_input.exercise_id,
                position=exercise_input.position,
                is_unilateral=exercise_input.is_unilateral,
                rest_seconds=exercise_input.rest_seconds,
                notes=exercise_input.notes,
            )
            await self.templates.add_template_exercise(new_te)
            for set_input in sorted(exercise_input.sets, key=lambda s: s.position):
                load_value_base = None
                if set_input.target_load_value is not None and set_input.target_load_unit_key:
                    unit = await self.workouts.get_weight_unit(set_input.target_load_unit_key)
                    load_value_base = to_base_value(set_input.target_load_value, unit)
                new_ts = WorkoutTemplateSet(
                    template_exercise_id=new_te.id,
                    position=set_input.position,
                    set_type=set_input.set_type,
                    target_reps_min=set_input.target_reps_min,
                    target_reps_max=set_input.target_reps_max,
                    target_load_value_input=set_input.target_load_value,
                    target_load_unit_key=set_input.target_load_unit_key,
                    target_load_value_base=load_value_base,
                    target_duration_seconds=set_input.target_duration_seconds,
                    target_rpe=set_input.target_rpe,
                    notes=set_input.notes,
                )
                await self.templates.add_template_set(new_ts)

        await self.db.commit()
        await self.db.refresh(version)
        return await self._build_version_response(version)

    async def publish_version(self, coach_id: UUID, version_id: UUID) -> TemplateVersionResponse:
        _, version = await self._get_owned_version(coach_id, version_id)
        if version.status != "draft":
            raise AppException("TEMPLATE_VERSION_IMMUTABLE", "This version has already been published.", 409)

        template_exercises = await self.templates.list_template_exercises(version.id)
        if not template_exercises:
            raise ValidationError("A template must contain at least one exercise before publishing")

        exercises_by_id = await self.exercise_repo.list_by_ids([te.exercise_id for te in template_exercises])
        sets_map = await self.templates.get_template_sets_map([te.id for te in template_exercises])
        for te in template_exercises:
            exercise = exercises_by_id.get(te.exercise_id)
            if not exercise or exercise.archived_at is not None:
                raise ValidationError("A template cannot be published while it references an archived exercise")
            if not sets_map.get(te.id):
                raise ValidationError("Every exercise must have at least one prescribed set before publishing")

        version.status = "published"
        version.published_at = datetime.now(UTC)
        await self.audit_logs.log(
            "workout_template.published",
            actor_user_id=coach_id,
            metadata={"templateVersionId": str(version.id), "templateId": str(version.template_id)},
        )
        await self.db.commit()
        await self.db.refresh(version)
        return await self._build_version_response(version)

    # -- Assignments -----------------------------------------------------

    def _derive_assignment_state(self, session: WorkoutSession | None) -> str:
        if session is None:
            return "available"
        return "completed" if session.status == "completed" else "in_progress"

    async def _assignment_response(
        self,
        assignment: WorkoutAssignment,
        version: WorkoutTemplateVersion,
        coach: User | None,
        session: WorkoutSession | None,
    ) -> AssignmentListItem:
        exercise_counts = await self.workouts.count_template_exercises_map([version.id])
        return AssignmentListItem(
            id=assignment.id,
            templateVersionId=version.id,
            title=version.title,
            coachName=f"{coach.first_name} {coach.last_name}".strip() if coach else "Coach",
            scheduledFor=assignment.scheduled_for,
            dueAt=assignment.due_at,
            notes=assignment.notes,
            exerciseCount=exercise_counts.get(version.id, 0),
            state=self._derive_assignment_state(session),
            assignedAt=assignment.assigned_at,
            sessionId=session.id if session else None,
        )

    async def create_assignment(
        self, coach: User, client_id: UUID, data: AssignmentCreateRequest
    ) -> AssignmentListItem:
        version = await self.templates.get_version(data.template_version_id)
        if not version:
            raise NotFoundError("Template version not found")
        template = await self.templates.get_template(version.template_id)
        if not template or template.coach_id != coach.id:
            raise NotFoundError("Template version not found")
        if version.status != "published":
            raise AppException("TEMPLATE_NOT_PUBLISHED", "Only a published template version can be assigned.", 409)

        assignment = WorkoutAssignment(
            template_version_id=version.id,
            client_id=client_id,
            assigned_by_user_id=coach.id,
            scheduled_for=data.scheduled_for,
            due_at=data.due_at,
            notes=data.notes,
        )
        await self.templates.add_assignment(assignment)
        await self.audit_logs.log(
            "workout_assignment.created",
            actor_user_id=coach.id,
            target_user_id=client_id,
            metadata={"assignmentId": str(assignment.id), "templateVersionId": str(version.id)},
        )
        await self.db.commit()
        await self.db.refresh(assignment)
        return await self._assignment_response(assignment, version, coach, None)

    async def cancel_assignment(self, coach_id: UUID, client_id: UUID, assignment_id: UUID) -> None:
        assignment = await self.templates.get_assignment_owned_by_coach(assignment_id, coach_id)
        if not assignment or assignment.client_id != client_id:
            raise NotFoundError("Workout assignment not found")
        existing_session = await self.workouts.get_session_by_assignment(assignment_id)
        if existing_session and existing_session.status == "completed":
            raise AppException(
                "ASSIGNMENT_ALREADY_COMPLETED", "A completed assignment cannot be canceled.", 409
            )
        if assignment.canceled_at is None:
            assignment.canceled_at = datetime.now(UTC)
            await self.audit_logs.log(
                "workout_assignment.canceled",
                actor_user_id=coach_id,
                target_user_id=client_id,
                metadata={"assignmentId": str(assignment.id)},
            )
            await self.db.commit()

    async def list_client_assignments(
        self, coach_id: UUID, client_id: UUID, cursor: str | None, page_size: int
    ) -> AssignmentListResponse:
        page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        cursor_assigned_at = None
        cursor_id = None
        if cursor:
            payload = decode_cursor(cursor)
            raw_assigned_at = payload.get("assignedAt")
            cursor_assigned_at = (
                datetime.fromisoformat(raw_assigned_at) if raw_assigned_at else None
            )
            raw_id = payload.get("id")
            cursor_id = UUID(raw_id) if raw_id else None

        rows = await self.templates.list_assignments_for_coach_client(
            coach_id, client_id, cursor_assigned_at, cursor_id, page_size + 1
        )
        has_more = len(rows) > page_size
        rows = rows[:page_size]

        items = []
        for assignment in rows:
            version = await self.templates.get_version(assignment.template_version_id)
            session = await self.workouts.get_session_by_assignment(assignment.id)
            coach = await self.users.get_by_id(coach_id)
            items.append(await self._assignment_response(assignment, version, coach, session))

        next_cursor = None
        if has_more and rows:
            last = rows[-1]
            next_cursor = encode_cursor(
                {"assignedAt": last.assigned_at.isoformat(), "id": str(last.id)}
            )
        return AssignmentListResponse(items=items, nextCursor=next_cursor)

    # -- Coach client history -------------------------------------------

    async def list_client_workouts(
        self, coach_id: UUID, client_id: UUID, cursor: str | None, page_size: int
    ) -> WorkoutHistoryListResponse:
        workout_service = WorkoutService(self.db)
        return await workout_service.list_history(client_id, cursor, page_size)

    async def get_client_workout_detail(self, coach_id: UUID, client_id: UUID, session_id: UUID):
        workout_service = WorkoutService(self.db)
        return await workout_service.get_session_detail(client_id, session_id)
