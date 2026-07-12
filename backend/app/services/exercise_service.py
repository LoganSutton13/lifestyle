from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.error_handlers import AppException, ForbiddenError, NotFoundError, ValidationError
from app.db.models.exercise import Exercise, ExerciseMuscleGroup
from app.db.models.exercise_equipment import ExerciseEquipment
from app.db.models.muscle_group import MuscleGroup
from app.db.models.user import User
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.exercises import ExerciseRepository
from app.repositories.workouts import WorkoutRepository
from app.schemas.exercises import (
    EquipmentInfo,
    ExerciseCreateRequest,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseSuggestionsResponse,
    ExerciseUpdateRequest,
    MuscleGroupInfo,
)
from app.services.text_utils import normalize_name, slugify

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 50
SUGGESTION_LIMIT = 3


class ExerciseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.exercises = ExerciseRepository(db)
        self.workouts = WorkoutRepository(db)
        self.audit_logs = AuditLogRepository(db)

    async def _build_response(
        self,
        exercise: Exercise,
        equipment_map: dict[str, ExerciseEquipment],
        muscle_map: dict[str, MuscleGroup],
        exercise_muscle_map: dict[UUID, list[ExerciseMuscleGroup]],
    ) -> ExerciseResponse:
        equipment = equipment_map.get(exercise.equipment_key)
        rows = exercise_muscle_map.get(exercise.id, [])
        primary = [
            MuscleGroupInfo(key=r.muscle_group_key, displayName=muscle_map[r.muscle_group_key].display_name)
            for r in rows
            if r.role == "primary" and r.muscle_group_key in muscle_map
        ]
        secondary = [
            MuscleGroupInfo(key=r.muscle_group_key, displayName=muscle_map[r.muscle_group_key].display_name)
            for r in rows
            if r.role == "secondary" and r.muscle_group_key in muscle_map
        ]
        return ExerciseResponse(
            id=exercise.id,
            name=exercise.name,
            slug=exercise.slug,
            equipment=EquipmentInfo(
                key=exercise.equipment_key,
                displayName=equipment.display_name if equipment else exercise.equipment_key,
            ),
            trackingType=exercise.tracking_type,
            defaultUnilateral=exercise.default_unilateral,
            defaultRestSeconds=exercise.default_rest_seconds,
            instructions=exercise.instructions,
            primaryMuscles=primary,
            secondaryMuscles=secondary,
            archivedAt=exercise.archived_at,
            createdByUserId=exercise.created_by_user_id,
        )

    async def _build_responses(self, exercises: list[Exercise]) -> list[ExerciseResponse]:
        equipment_map = await self.exercises.list_equipment_map()
        muscle_map = await self.exercises.list_muscle_groups_map()
        exercise_muscle_map = await self.exercises.get_muscle_groups_for_exercises([e.id for e in exercises])
        return [
            await self._build_response(exercise, equipment_map, muscle_map, exercise_muscle_map)
            for exercise in exercises
        ]

    async def search(
        self,
        current_user: User,
        query: str | None,
        equipment_key: str | None,
        muscle_group_key: str | None,
        include_archived: bool,
        cursor: str | None,
        page_size: int,
    ) -> ExerciseListResponse:
        from app.core.cursor import decode_cursor, encode_cursor

        page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        if include_archived and current_user.role != "admin":
            include_archived = False

        cursor_name: str | None = None
        cursor_id: UUID | None = None
        if cursor:
            payload = decode_cursor(cursor)
            cursor_name = payload.get("name")
            raw_id = payload.get("id")
            cursor_id = UUID(raw_id) if raw_id else None

        rows = await self.exercises.search(
            query, equipment_key, muscle_group_key, include_archived, cursor_name, cursor_id, page_size + 1
        )
        has_more = len(rows) > page_size
        rows = rows[:page_size]
        items = await self._build_responses(rows)
        next_cursor = None
        if has_more and rows:
            last = rows[-1]
            next_cursor = encode_cursor({"name": last.normalized_name, "id": str(last.id)})
        return ExerciseListResponse(items=items, nextCursor=next_cursor)

    async def get_suggestions(self, client_id: UUID, session_id: UUID, limit: int = SUGGESTION_LIMIT) -> ExerciseSuggestionsResponse:
        session = await self.workouts.get_session_for_client(session_id, client_id)
        if not session:
            raise NotFoundError("Workout session not found")
        limit = max(1, min(limit, SUGGESTION_LIMIT))

        existing_rows = await self.workouts.list_session_exercises(session_id)
        existing_ids = {row.exercise_id for row in existing_rows}

        recent_ids = await self.workouts.recent_exercise_ids_for_client(client_id, limit=limit + len(existing_ids))
        recent_ids = [rid for rid in recent_ids if rid not in existing_ids][:limit]

        exercises_by_id = await self.exercises.list_by_ids(recent_ids)
        selected = [exercises_by_id[rid] for rid in recent_ids if rid in exercises_by_id and exercises_by_id[rid].archived_at is None]

        remaining = limit - len(selected)
        if remaining > 0:
            exclude = existing_ids | {e.id for e in selected}
            fillers = await self.exercises.list_alpha_active(exclude, remaining)
            selected.extend(fillers)

        items = await self._build_responses(selected[:limit])
        return ExerciseSuggestionsResponse(items=items)

    def _assert_can_manage(self, current_user: User, exercise: Exercise) -> None:
        if current_user.role == "admin":
            return
        if current_user.role == "coach" and exercise.created_by_user_id == current_user.id:
            return
        raise ForbiddenError("You do not have permission to modify this exercise")

    async def create_exercise(self, current_user: User, data: ExerciseCreateRequest) -> ExerciseResponse:
        equipment = await self.exercises.get_equipment(data.equipment_key)
        if not equipment:
            raise ValidationError("Invalid equipmentKey")
        if not data.primary_muscle_keys:
            raise ValidationError("At least one primary muscle group is required")
        if not await self.exercises.muscle_groups_exist(data.primary_muscle_keys):
            raise ValidationError("One or more primaryMuscleKeys are invalid")
        if data.secondary_muscle_keys and not await self.exercises.muscle_groups_exist(data.secondary_muscle_keys):
            raise ValidationError("One or more secondaryMuscleKeys are invalid")

        normalized = normalize_name(data.name)
        duplicate = await self.exercises.find_duplicate(normalized, data.equipment_key)
        if duplicate:
            raise AppException(
                "DUPLICATE_EXERCISE",
                "An exercise with this name and equipment already exists",
                409,
                details={"existingExerciseId": str(duplicate.id)},
            )

        base_slug = slugify(data.name)
        slug = base_slug
        suffix = 2
        while await self.exercises.get_by_slug(slug):
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        exercise = Exercise(
            slug=slug,
            name=data.name,
            normalized_name=normalized,
            equipment_key=data.equipment_key,
            tracking_type=data.tracking_type,
            default_unilateral=data.default_unilateral,
            default_rest_seconds=data.default_rest_seconds,
            instructions=data.instructions,
            created_by_user_id=current_user.id,
        )
        await self.exercises.add(exercise)
        await self.exercises.replace_muscle_groups(exercise.id, data.primary_muscle_keys, data.secondary_muscle_keys)
        await self.audit_logs.log(
            "exercise.created",
            actor_user_id=current_user.id,
            metadata={"exerciseId": str(exercise.id), "name": exercise.name},
        )
        await self.db.commit()
        await self.db.refresh(exercise)
        equipment_map = await self.exercises.list_equipment_map()
        muscle_map = await self.exercises.list_muscle_groups_map()
        exercise_muscle_map = await self.exercises.get_muscle_groups_for_exercises([exercise.id])
        return await self._build_response(exercise, equipment_map, muscle_map, exercise_muscle_map)

    async def update_exercise(
        self, current_user: User, exercise_id: UUID, data: ExerciseUpdateRequest
    ) -> ExerciseResponse:
        exercise = await self.exercises.get_by_id(exercise_id)
        if not exercise:
            raise NotFoundError("Exercise not found")
        self._assert_can_manage(current_user, exercise)

        referenced = await self.exercises.is_referenced(exercise_id)

        if data.tracking_type is not None and data.tracking_type != exercise.tracking_type:
            if referenced:
                raise AppException(
                    "VALIDATION_ERROR",
                    "Tracking type cannot be changed once an exercise has been used in a template or session",
                    400,
                )
            exercise.tracking_type = data.tracking_type

        if data.equipment_key is not None and data.equipment_key != exercise.equipment_key:
            if referenced:
                raise AppException(
                    "VALIDATION_ERROR",
                    "Equipment cannot be changed once an exercise has been used in a template or session",
                    400,
                )
            equipment = await self.exercises.get_equipment(data.equipment_key)
            if not equipment:
                raise ValidationError("Invalid equipmentKey")
            exercise.equipment_key = data.equipment_key

        if data.name is not None:
            exercise.name = data.name
            exercise.normalized_name = normalize_name(data.name)

        duplicate = await self.exercises.find_duplicate(
            exercise.normalized_name, exercise.equipment_key, exclude_id=exercise.id
        )
        if duplicate:
            raise AppException(
                "DUPLICATE_EXERCISE",
                "An exercise with this name and equipment already exists",
                409,
                details={"existingExerciseId": str(duplicate.id)},
            )

        if data.default_unilateral is not None:
            exercise.default_unilateral = data.default_unilateral
        if data.default_rest_seconds is not None:
            exercise.default_rest_seconds = data.default_rest_seconds
        if data.instructions is not None:
            exercise.instructions = data.instructions

        if data.primary_muscle_keys is not None or data.secondary_muscle_keys is not None:
            current_rows = await self.exercises.get_muscle_groups_for_exercises([exercise.id])
            existing = current_rows.get(exercise.id, [])
            primary_keys = data.primary_muscle_keys
            if primary_keys is None:
                primary_keys = [r.muscle_group_key for r in existing if r.role == "primary"]
            secondary_keys = data.secondary_muscle_keys
            if secondary_keys is None:
                secondary_keys = [r.muscle_group_key for r in existing if r.role == "secondary"]
            if not primary_keys:
                raise ValidationError("At least one primary muscle group is required")
            if not await self.exercises.muscle_groups_exist(primary_keys):
                raise ValidationError("One or more primaryMuscleKeys are invalid")
            if secondary_keys and not await self.exercises.muscle_groups_exist(secondary_keys):
                raise ValidationError("One or more secondaryMuscleKeys are invalid")
            await self.exercises.replace_muscle_groups(exercise.id, primary_keys, secondary_keys)

        await self.audit_logs.log(
            "exercise.updated",
            actor_user_id=current_user.id,
            metadata={"exerciseId": str(exercise.id)},
        )
        await self.db.commit()
        await self.db.refresh(exercise)
        equipment_map = await self.exercises.list_equipment_map()
        muscle_map = await self.exercises.list_muscle_groups_map()
        exercise_muscle_map = await self.exercises.get_muscle_groups_for_exercises([exercise.id])
        return await self._build_response(exercise, equipment_map, muscle_map, exercise_muscle_map)

    async def archive_exercise(self, current_user: User, exercise_id: UUID) -> ExerciseResponse:
        from datetime import UTC, datetime

        exercise = await self.exercises.get_by_id(exercise_id)
        if not exercise:
            raise NotFoundError("Exercise not found")
        self._assert_can_manage(current_user, exercise)
        if exercise.archived_at is None:
            exercise.archived_at = datetime.now(UTC)
            await self.audit_logs.log(
                "exercise.archived",
                actor_user_id=current_user.id,
                metadata={"exerciseId": str(exercise.id)},
            )
            await self.db.commit()
            await self.db.refresh(exercise)
        equipment_map = await self.exercises.list_equipment_map()
        muscle_map = await self.exercises.list_muscle_groups_map()
        exercise_muscle_map = await self.exercises.get_muscle_groups_for_exercises([exercise.id])
        return await self._build_response(exercise, equipment_map, muscle_map, exercise_muscle_map)

    async def restore_exercise(self, current_user: User, exercise_id: UUID) -> ExerciseResponse:
        exercise = await self.exercises.get_by_id(exercise_id)
        if not exercise:
            raise NotFoundError("Exercise not found")
        if exercise.archived_at is not None:
            exercise.archived_at = None
            await self.audit_logs.log(
                "exercise.restored",
                actor_user_id=current_user.id,
                metadata={"exerciseId": str(exercise.id)},
            )
            await self.db.commit()
            await self.db.refresh(exercise)
        equipment_map = await self.exercises.list_equipment_map()
        muscle_map = await self.exercises.list_muscle_groups_map()
        exercise_muscle_map = await self.exercises.get_muscle_groups_for_exercises([exercise.id])
        return await self._build_response(exercise, equipment_map, muscle_map, exercise_muscle_map)
