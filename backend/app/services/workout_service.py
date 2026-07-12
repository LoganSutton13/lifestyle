from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import AppException, NotFoundError, ValidationError
from app.core.cursor import decode_cursor, encode_cursor
from app.db.models.user import User
from app.db.models.workout_session import WorkoutSession, WorkoutSessionExercise, WorkoutSet
from app.db.models.workout_template import WorkoutTemplateSet
from app.repositories.exercises import ExerciseRepository
from app.repositories.workouts import WorkoutRepository
from app.schemas.exercises import EquipmentInfo
from app.schemas.workouts import (
    ActiveWorkoutResponse,
    AddExerciseRequest,
    AddSetRequest,
    AssignmentListItem,
    AssignmentListResponse,
    AssignmentRefResponse,
    CompleteWorkoutRequest,
    ExerciseOrderRequest,
    ExerciseSummary,
    PrescriptionResponse,
    PrescriptionSetResponse,
    SessionExerciseResponse,
    SessionUpdateRequest,
    StartWorkoutRequest,
    UpdateSessionExerciseRequest,
    UpdateSetRequest,
    WorkoutHistoryItem,
    WorkoutHistoryListResponse,
    WorkoutSessionDetailResponse,
    WorkoutSetResponse,
)
from app.services.unit_conversion import to_base_value

MAX_EXERCISES_PER_SESSION = 40
MAX_SETS_PER_EXERCISE = 50
DEFAULT_HISTORY_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50


class WorkoutService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.workouts = WorkoutRepository(db)
        self.exercise_repo = ExerciseRepository(db)

    # -- Response building -------------------------------------------------

    @staticmethod
    def _prescription_set_response(ts: WorkoutTemplateSet) -> PrescriptionSetResponse:
        return PrescriptionSetResponse(
            id=ts.id,
            position=ts.position,
            setType=ts.set_type,
            targetRepsMin=ts.target_reps_min,
            targetRepsMax=ts.target_reps_max,
            targetLoadValue=str(ts.target_load_value_input) if ts.target_load_value_input is not None else None,
            targetLoadUnitKey=ts.target_load_unit_key,
            targetDurationSeconds=ts.target_duration_seconds,
            targetRpe=str(ts.target_rpe) if ts.target_rpe is not None else None,
        )

    @staticmethod
    def _set_response(s: WorkoutSet) -> WorkoutSetResponse:
        return WorkoutSetResponse(
            id=s.id,
            position=s.position,
            setType=s.set_type,
            reps=s.reps,
            loadValue=str(s.load_value_input) if s.load_value_input is not None else None,
            loadUnitKey=s.load_unit_key,
            durationSeconds=s.duration_seconds,
            rpe=str(s.rpe) if s.rpe is not None else None,
            completedAt=s.completed_at,
        )

    async def _exercise_summary(self, exercise, equipment_map) -> ExerciseSummary:
        equipment = equipment_map.get(exercise.equipment_key)
        return ExerciseSummary(
            id=exercise.id,
            name=exercise.name,
            trackingType=exercise.tracking_type,
            equipment=EquipmentInfo(
                key=exercise.equipment_key,
                displayName=equipment.display_name if equipment else exercise.equipment_key,
            ),
        )

    async def _build_full_session_exercise_response(self, row: WorkoutSessionExercise) -> SessionExerciseResponse:
        exercise = await self.exercise_repo.get_by_id(row.exercise_id)
        equipment_map = await self.exercise_repo.list_equipment_map()
        exercise_summary = await self._exercise_summary(exercise, equipment_map)
        prescription = None
        if row.source_template_exercise_id:
            tex_map = await self.workouts.get_template_exercises_map([row.source_template_exercise_id])
            tex = tex_map.get(row.source_template_exercise_id)
            if tex:
                tsets = await self.workouts.list_template_sets(tex.id)
                prescription = PrescriptionResponse(
                    notes=tex.notes,
                    sets=[self._prescription_set_response(ts) for ts in tsets],
                )
        sets = await self.workouts.list_sets(row.id)
        return SessionExerciseResponse(
            id=row.id,
            position=row.position,
            isUnilateral=row.is_unilateral,
            restSeconds=row.rest_seconds,
            notes=row.notes,
            exercise=exercise_summary,
            prescription=prescription,
            sets=[self._set_response(s) for s in sets],
        )

    async def build_session_detail_response(self, session: WorkoutSession) -> WorkoutSessionDetailResponse:
        exercise_rows = await self.workouts.list_session_exercises(session.id)
        exercises_by_id = await self.exercise_repo.list_by_ids([row.exercise_id for row in exercise_rows])
        equipment_map = await self.exercise_repo.list_equipment_map()
        sets_map = await self.workouts.list_sets_for_session(session.id)

        template_exercise_ids = [row.source_template_exercise_id for row in exercise_rows if row.source_template_exercise_id]
        template_exercise_map = await self.workouts.get_template_exercises_map(template_exercise_ids)
        template_sets_map = await self.workouts.get_template_sets_map(template_exercise_ids)

        exercise_responses: list[SessionExerciseResponse] = []
        for row in exercise_rows:
            exercise = exercises_by_id.get(row.exercise_id)
            if exercise is None:
                continue
            prescription = None
            if row.source_template_exercise_id and row.source_template_exercise_id in template_exercise_map:
                tex = template_exercise_map[row.source_template_exercise_id]
                tsets = template_sets_map.get(row.source_template_exercise_id, [])
                prescription = PrescriptionResponse(
                    notes=tex.notes,
                    sets=[self._prescription_set_response(ts) for ts in tsets],
                )
            sets = sets_map.get(row.id, [])
            exercise_responses.append(
                SessionExerciseResponse(
                    id=row.id,
                    position=row.position,
                    isUnilateral=row.is_unilateral,
                    restSeconds=row.rest_seconds,
                    notes=row.notes,
                    exercise=await self._exercise_summary(exercise, equipment_map),
                    prescription=prescription,
                    sets=[self._set_response(s) for s in sets],
                )
            )

        assignment_ref = None
        if session.assignment_id:
            assignment = await self.workouts.get_assignment(session.assignment_id)
            if assignment:
                assignment_ref = AssignmentRefResponse(
                    id=assignment.id,
                    scheduledFor=assignment.scheduled_for,
                    templateVersionId=assignment.template_version_id,
                )

        return WorkoutSessionDetailResponse(
            id=session.id,
            source=session.source,
            status=session.status,
            title=session.title,
            startedAt=session.started_at,
            completedAt=session.completed_at,
            notes=session.notes,
            assignment=assignment_ref,
            exercises=exercise_responses,
        )

    # -- Ownership / state guards -----------------------------------------

    async def _get_active_owned_session(self, client_id: UUID, session_id: UUID) -> WorkoutSession:
        session = await self.workouts.get_session_for_client(session_id, client_id)
        if not session:
            raise NotFoundError("Workout session not found")
        if session.status == "completed":
            raise AppException("WORKOUT_ALREADY_COMPLETED", "This workout has already been completed.", 409)
        return session

    # -- Active / detail ----------------------------------------------------

    async def get_active(self, client_id: UUID) -> ActiveWorkoutResponse:
        session = await self.workouts.get_active_session(client_id)
        if not session:
            return ActiveWorkoutResponse(session=None)
        return ActiveWorkoutResponse(session=await self.build_session_detail_response(session))

    async def get_session_detail(self, client_id: UUID, session_id: UUID) -> WorkoutSessionDetailResponse:
        session = await self.workouts.get_session_for_client(session_id, client_id)
        if not session:
            raise NotFoundError("Workout session not found")
        return await self.build_session_detail_response(session)

    async def update_session_metadata(
        self, client_id: UUID, session_id: UUID, data: SessionUpdateRequest
    ) -> WorkoutSessionDetailResponse:
        session = await self._get_active_owned_session(client_id, session_id)
        if data.title is not None:
            session.title = data.title
        if data.notes is not None:
            session.notes = data.notes
        await self.db.commit()
        await self.db.refresh(session)
        return await self.build_session_detail_response(session)

    # -- Start ----------------------------------------------------------

    async def start_workout(self, client_id: UUID, data: StartWorkoutRequest) -> WorkoutSessionDetailResponse:
        if data.mode == "freestyle":
            return await self._start_freestyle(client_id)
        if data.assignment_id is None:
            raise ValidationError("assignmentId is required to start an assigned workout")
        return await self._start_assigned(client_id, data.assignment_id)

    async def _start_freestyle(self, client_id: UUID) -> WorkoutSessionDetailResponse:
        existing = await self.workouts.get_active_session(client_id)
        if existing:
            raise AppException(
                "ACTIVE_WORKOUT_EXISTS",
                "You already have an active workout.",
                409,
                details={"sessionId": str(existing.id)},
            )
        session = WorkoutSession(client_id=client_id, source="freestyle", status="in_progress")
        await self.workouts.add_session(session)
        await self.db.commit()
        await self.db.refresh(session)
        return await self.build_session_detail_response(session)

    async def _start_assigned(self, client_id: UUID, assignment_id: UUID) -> WorkoutSessionDetailResponse:
        assignment = await self.workouts.lock_assignment(assignment_id)
        if not assignment or assignment.client_id != client_id:
            raise NotFoundError("Workout assignment not found")
        if assignment.canceled_at is not None:
            raise AppException("ASSIGNMENT_NOT_AVAILABLE", "This assignment has been canceled.", 409)

        version = await self.workouts.get_template_version(assignment.template_version_id)
        if not version or version.status != "published":
            raise AppException("TEMPLATE_NOT_PUBLISHED", "The assigned template version is not published.", 409)

        existing_session = await self.workouts.get_session_by_assignment(assignment_id)
        if existing_session:
            if existing_session.status == "in_progress":
                return await self.build_session_detail_response(existing_session)
            raise AppException(
                "ASSIGNMENT_ALREADY_COMPLETED", "This assignment has already been completed.", 409
            )

        active = await self.workouts.get_active_session(client_id)
        if active:
            raise AppException(
                "ACTIVE_WORKOUT_EXISTS",
                "You already have an active workout.",
                409,
                details={"sessionId": str(active.id)},
            )

        template_exercises = await self.workouts.list_template_exercises(version.id)
        if not template_exercises:
            raise AppException(
                "ASSIGNMENT_NOT_AVAILABLE", "This assignment has no exercises and cannot be started.", 409
            )

        session = WorkoutSession(
            client_id=client_id,
            assignment_id=assignment.id,
            source="assigned",
            status="in_progress",
            title=version.title,
        )
        await self.workouts.add_session(session)

        for position, template_exercise in enumerate(template_exercises):
            session_exercise = WorkoutSessionExercise(
                session_id=session.id,
                exercise_id=template_exercise.exercise_id,
                source_template_exercise_id=template_exercise.id,
                position=position,
                is_unilateral=template_exercise.is_unilateral,
                rest_seconds=template_exercise.rest_seconds,
                notes="",
            )
            await self.workouts.add_session_exercise(session_exercise)
            template_sets = await self.workouts.list_template_sets(template_exercise.id)
            for set_position, template_set in enumerate(template_sets):
                draft_set = WorkoutSet(
                    session_exercise_id=session_exercise.id,
                    source_template_set_id=template_set.id,
                    position=set_position,
                    set_type=template_set.set_type,
                )
                await self.workouts.add_set(draft_set)

        await self.db.commit()
        await self.db.refresh(session)
        return await self.build_session_detail_response(session)

    # -- Exercises --------------------------------------------------------

    async def add_exercise(
        self, client_id: UUID, session_id: UUID, data: AddExerciseRequest
    ) -> SessionExerciseResponse:
        await self._get_active_owned_session(client_id, session_id)
        exercise = await self.exercise_repo.get_by_id(data.exercise_id)
        if not exercise:
            raise NotFoundError("Exercise not found")
        if exercise.archived_at is not None:
            raise AppException("EXERCISE_ARCHIVED", "This exercise has been archived and cannot be added.", 400)
        count = await self.workouts.count_exercises(session_id)
        if count >= MAX_EXERCISES_PER_SESSION:
            raise AppException(
                "EXERCISE_LIMIT_REACHED", "This workout has reached the maximum of 40 exercises.", 400
            )
        position = await self.workouts.next_exercise_position(session_id)
        row = WorkoutSessionExercise(
            session_id=session_id,
            exercise_id=exercise.id,
            position=position,
            is_unilateral=exercise.default_unilateral,
            rest_seconds=exercise.default_rest_seconds,
        )
        await self.workouts.add_session_exercise(row)
        await self.db.commit()
        await self.db.refresh(row)
        return await self._build_full_session_exercise_response(row)

    async def update_session_exercise(
        self, client_id: UUID, session_id: UUID, session_exercise_id: UUID, data: UpdateSessionExerciseRequest
    ) -> SessionExerciseResponse:
        await self._get_active_owned_session(client_id, session_id)
        row = await self.workouts.get_session_exercise(session_exercise_id, session_id)
        if not row:
            raise NotFoundError("Session exercise not found")
        if data.is_unilateral is not None:
            row.is_unilateral = data.is_unilateral
        if data.rest_seconds is not None:
            row.rest_seconds = data.rest_seconds
        if data.notes is not None:
            row.notes = data.notes
        await self.db.commit()
        await self.db.refresh(row)
        return await self._build_full_session_exercise_response(row)

    async def remove_session_exercise(self, client_id: UUID, session_id: UUID, session_exercise_id: UUID) -> None:
        await self._get_active_owned_session(client_id, session_id)
        row = await self.workouts.get_session_exercise(session_exercise_id, session_id)
        if not row:
            raise NotFoundError("Session exercise not found")
        await self.workouts.delete_session_exercise_cascade(row)
        await self.db.commit()

    async def reorder_exercises(
        self, client_id: UUID, session_id: UUID, data: ExerciseOrderRequest
    ) -> list[SessionExerciseResponse]:
        await self._get_active_owned_session(client_id, session_id)
        current_rows = await self.workouts.list_session_exercises(session_id)
        current_ids = {row.id for row in current_rows}
        submitted_ids = data.exercise_ids
        if len(submitted_ids) != len(set(submitted_ids)) or set(submitted_ids) != current_ids:
            raise AppException(
                "INVALID_EXERCISE_ORDER",
                "The submitted order must contain every current session exercise exactly once.",
                400,
            )
        await self.workouts.reorder_session_exercises(session_id, submitted_ids)
        await self.db.commit()
        updated_rows = await self.workouts.list_session_exercises(session_id)
        return [await self._build_full_session_exercise_response(row) for row in updated_rows]

    # -- Sets ---------------------------------------------------------------

    def _validate_completion_metrics(self, tracking_type: str, set_row: WorkoutSet) -> None:
        if tracking_type == "reps_load":
            if set_row.reps is None:
                raise AppException("INVALID_SET_METRICS", "Reps are required to complete this set.", 400)
            if set_row.load_value_input is None:
                raise AppException("INVALID_SET_METRICS", "Load is required to complete this set.", 400)
        elif tracking_type == "reps_only":
            if set_row.reps is None:
                raise AppException("INVALID_SET_METRICS", "Reps are required to complete this set.", 400)
        elif tracking_type == "duration":
            if set_row.duration_seconds is None:
                raise AppException("INVALID_SET_METRICS", "Duration is required to complete this set.", 400)

    async def add_set(
        self, client_id: UUID, session_id: UUID, session_exercise_id: UUID, data: AddSetRequest
    ) -> WorkoutSetResponse:
        await self._get_active_owned_session(client_id, session_id)
        row = await self.workouts.get_session_exercise(session_exercise_id, session_id)
        if not row:
            raise NotFoundError("Session exercise not found")
        count = await self.workouts.count_sets(session_exercise_id)
        if count >= MAX_SETS_PER_EXERCISE:
            raise AppException("SET_LIMIT_REACHED", "This exercise has reached the maximum of 50 sets.", 400)

        load_value_base = None
        load_unit_key = None
        if data.load_value is not None:
            if not data.load_unit_key:
                raise ValidationError("loadUnitKey is required when loadValue is provided")
            unit = await self.workouts.get_weight_unit(data.load_unit_key)
            if not unit:
                raise ValidationError("loadUnitKey must reference a valid weight unit")
            load_value_base = to_base_value(data.load_value, unit)
            load_unit_key = data.load_unit_key

        position = await self.workouts.next_set_position(session_exercise_id)
        set_row = WorkoutSet(
            session_exercise_id=session_exercise_id,
            position=position,
            set_type=data.set_type,
            reps=data.reps,
            load_value_input=data.load_value,
            load_unit_key=load_unit_key,
            load_value_base=load_value_base,
            duration_seconds=data.duration_seconds,
            rpe=data.rpe,
        )
        await self.workouts.add_set(set_row)
        await self.db.commit()
        await self.db.refresh(set_row)
        return self._set_response(set_row)

    async def update_set(
        self,
        client_id: UUID,
        session_id: UUID,
        session_exercise_id: UUID,
        set_id: UUID,
        data: UpdateSetRequest,
    ) -> WorkoutSetResponse:
        await self._get_active_owned_session(client_id, session_id)
        exercise_row = await self.workouts.get_session_exercise(session_exercise_id, session_id)
        if not exercise_row:
            raise NotFoundError("Session exercise not found")
        set_row = await self.workouts.get_set(set_id, session_exercise_id)
        if not set_row:
            raise NotFoundError("Set not found")

        fields = data.model_dump(exclude_unset=True)

        if fields.get("set_type") is not None:
            set_row.set_type = fields["set_type"]
        if "reps" in fields:
            set_row.reps = fields["reps"]
        if "duration_seconds" in fields:
            set_row.duration_seconds = fields["duration_seconds"]
        if "rpe" in fields:
            set_row.rpe = fields["rpe"]

        if "load_value" in fields or "load_unit_key" in fields:
            new_load_value = fields.get("load_value", set_row.load_value_input)
            new_unit_key = fields.get("load_unit_key", set_row.load_unit_key)
            if new_load_value is None:
                set_row.load_value_input = None
                set_row.load_unit_key = None
                set_row.load_value_base = None
            else:
                if not new_unit_key:
                    raise ValidationError("loadUnitKey is required when loadValue is provided")
                unit = await self.workouts.get_weight_unit(new_unit_key)
                if not unit:
                    raise ValidationError("loadUnitKey must reference a valid weight unit")
                set_row.load_value_input = new_load_value
                set_row.load_unit_key = new_unit_key
                set_row.load_value_base = to_base_value(new_load_value, unit)

        completed = fields.get("completed")
        if completed is True and set_row.completed_at is None:
            exercise = await self.exercise_repo.get_by_id(exercise_row.exercise_id)
            self._validate_completion_metrics(exercise.tracking_type, set_row)
            set_row.completed_at = datetime.now(UTC)
        elif completed is False:
            set_row.completed_at = None

        await self.db.commit()
        await self.db.refresh(set_row)
        return self._set_response(set_row)

    async def delete_set(self, client_id: UUID, session_id: UUID, session_exercise_id: UUID, set_id: UUID) -> None:
        await self._get_active_owned_session(client_id, session_id)
        exercise_row = await self.workouts.get_session_exercise(session_exercise_id, session_id)
        if not exercise_row:
            raise NotFoundError("Session exercise not found")
        set_row = await self.workouts.get_set(set_id, session_exercise_id)
        if not set_row:
            raise NotFoundError("Set not found")
        await self.workouts.delete_set(set_row)
        await self.db.flush()
        await self.workouts.renumber_sets(session_exercise_id)
        await self.db.commit()

    # -- Completion / discard ---------------------------------------------

    async def complete_workout(
        self, client_id: UUID, session_id: UUID, data: CompleteWorkoutRequest
    ) -> WorkoutSessionDetailResponse:
        session = await self.workouts.lock_session_for_client(session_id, client_id)
        if not session:
            raise NotFoundError("Workout session not found")
        if session.status == "completed":
            return await self.build_session_detail_response(session)

        if data.notes is not None:
            session.notes = data.notes

        await self.workouts.delete_incomplete_sets(session_id)
        await self.db.flush()
        await self.workouts.delete_empty_session_exercises(session_id)
        await self.db.flush()

        completed_count = await self.workouts.count_completed_sets(session_id)
        if completed_count == 0:
            await self.db.rollback()
            raise AppException(
                "WORKOUT_HAS_NO_COMPLETED_SETS",
                "This workout has no completed sets and cannot be finished. Discard it instead.",
                409,
            )

        session.status = "completed"
        session.completed_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(session)
        return await self.build_session_detail_response(session)

    async def discard_workout(self, client_id: UUID, session_id: UUID) -> None:
        session = await self.workouts.get_session_for_client(session_id, client_id)
        if not session:
            raise NotFoundError("Workout session not found")
        if session.status == "completed":
            raise AppException("WORKOUT_ALREADY_COMPLETED", "Completed workouts cannot be discarded.", 409)
        await self.workouts.delete_session_cascade(session)
        await self.db.commit()

    # -- History --------------------------------------------------------

    async def list_history(self, client_id: UUID, cursor: str | None, page_size: int) -> WorkoutHistoryListResponse:
        page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        cursor_started_at = None
        cursor_id = None
        if cursor:
            payload = decode_cursor(cursor)
            raw_started_at = payload.get("startedAt")
            cursor_started_at = datetime.fromisoformat(raw_started_at) if raw_started_at else None
            raw_id = payload.get("id")
            cursor_id = UUID(raw_id) if raw_id else None

        sessions = await self.workouts.list_history(client_id, cursor_started_at, cursor_id, page_size + 1)
        has_more = len(sessions) > page_size
        sessions = sessions[:page_size]
        counts = await self.workouts.session_aggregate_counts([s.id for s in sessions])

        items = []
        for session in sessions:
            exercise_count, completed_set_count = counts.get(session.id, (0, 0))
            duration_seconds = (
                int((session.completed_at - session.started_at).total_seconds()) if session.completed_at else 0
            )
            items.append(
                WorkoutHistoryItem(
                    id=session.id,
                    source=session.source,
                    title=session.title,
                    startedAt=session.started_at,
                    completedAt=session.completed_at,
                    durationSeconds=duration_seconds,
                    exerciseCount=exercise_count,
                    completedSetCount=completed_set_count,
                )
            )

        next_cursor = None
        if has_more and sessions:
            last = sessions[-1]
            next_cursor = encode_cursor({"startedAt": last.started_at.isoformat(), "id": str(last.id)})
        return WorkoutHistoryListResponse(items=items, nextCursor=next_cursor)

    # -- Assignments (client-facing) ---------------------------------------

    def _derive_assignment_state(self, session: WorkoutSession | None, canceled: bool) -> str:
        if session is None:
            return "available"
        if session.status == "completed":
            return "completed"
        return "in_progress"

    async def _assignment_item(
        self, assignment, version, coach: User | None, session: WorkoutSession | None, exercise_count: int
    ) -> AssignmentListItem:
        return AssignmentListItem(
            id=assignment.id,
            templateVersionId=version.id,
            title=version.title,
            coachName=f"{coach.first_name} {coach.last_name}".strip() if coach else "Coach",
            scheduledFor=assignment.scheduled_for,
            dueAt=assignment.due_at,
            notes=assignment.notes,
            exerciseCount=exercise_count,
            state=self._derive_assignment_state(session, assignment.canceled_at is not None),
            assignedAt=assignment.assigned_at,
            sessionId=session.id if session else None,
        )

    async def list_assignments(
        self, client_id: UUID, state: str | None, cursor: str | None, page_size: int
    ) -> AssignmentListResponse:
        page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        cursor_assigned_at = None
        cursor_id = None
        if cursor:
            payload = decode_cursor(cursor)
            raw_assigned_at = payload.get("assignedAt")
            cursor_assigned_at = datetime.fromisoformat(raw_assigned_at) if raw_assigned_at else None
            raw_id = payload.get("id")
            cursor_id = UUID(raw_id) if raw_id else None

        rows = await self.workouts.list_assignments_for_client(
            client_id, state, cursor_assigned_at, cursor_id, page_size + 1
        )
        has_more = len(rows) > page_size
        rows = rows[:page_size]
        version_ids = [version.id for _, version, _, _ in rows]
        exercise_counts = await self.workouts.count_template_exercises_map(version_ids)

        items = [
            await self._assignment_item(assignment, version, coach, session, exercise_counts.get(version.id, 0))
            for assignment, version, coach, session in rows
        ]
        next_cursor = None
        if has_more and rows:
            last_assignment = rows[-1][0]
            next_cursor = encode_cursor(
                {"assignedAt": last_assignment.assigned_at.isoformat(), "id": str(last_assignment.id)}
            )
        return AssignmentListResponse(items=items, nextCursor=next_cursor)

    async def get_assignment_detail(self, client_id: UUID, assignment_id: UUID) -> AssignmentListItem:
        row = await self.workouts.get_assignment_with_version(assignment_id)
        if not row:
            raise NotFoundError("Workout assignment not found")
        assignment, version, coach, session = row
        if assignment.client_id != client_id:
            raise NotFoundError("Workout assignment not found")
        exercise_counts = await self.workouts.count_template_exercises_map([version.id])
        return await self._assignment_item(assignment, version, coach, session, exercise_counts.get(version.id, 0))
