import { apiRequest } from '../../lib/apiClient'
import type {
  ActiveWorkoutResponse,
  AddSetRequest,
  AssignmentListItem,
  AssignmentListResponse,
  AssignmentState,
  CompleteWorkoutRequest,
  CursorPageParams,
  SessionExercise,
  SessionUpdateRequest,
  StartWorkoutRequest,
  UpdateSessionExerciseRequest,
  UpdateSetRequest,
  WorkoutHistoryListResponse,
  WorkoutSession,
  WorkoutSet,
} from './types'

export function fetchActiveWorkout(): Promise<ActiveWorkoutResponse> {
  return apiRequest<ActiveWorkoutResponse>('/api/me/workouts/active')
}

export function startWorkout(body: StartWorkoutRequest): Promise<WorkoutSession> {
  return apiRequest<WorkoutSession>('/api/me/workouts', {
    method: 'POST',
    body,
  })
}

export function fetchWorkoutHistory(params: CursorPageParams = {}): Promise<WorkoutHistoryListResponse> {
  const search = new URLSearchParams()
  search.set('pageSize', String(params.pageSize ?? 20))
  if (params.cursor) {
    search.set('cursor', params.cursor)
  }
  return apiRequest<WorkoutHistoryListResponse>(`/api/me/workouts?${search.toString()}`)
}

export function fetchWorkoutSession(sessionId: string): Promise<WorkoutSession> {
  return apiRequest<WorkoutSession>(`/api/me/workouts/${sessionId}`)
}

export function updateWorkoutSession(
  sessionId: string,
  body: SessionUpdateRequest,
): Promise<WorkoutSession> {
  return apiRequest<WorkoutSession>(`/api/me/workouts/${sessionId}`, {
    method: 'PATCH',
    body,
  })
}

export function discardWorkout(sessionId: string): Promise<void> {
  return apiRequest<void>(`/api/me/workouts/${sessionId}`, {
    method: 'DELETE',
  })
}

export function completeWorkout(
  sessionId: string,
  body: CompleteWorkoutRequest = {},
): Promise<WorkoutSession> {
  return apiRequest<WorkoutSession>(`/api/me/workouts/${sessionId}/complete`, {
    method: 'POST',
    body,
  })
}

export function addSessionExercise(sessionId: string, exerciseId: string): Promise<SessionExercise> {
  return apiRequest<SessionExercise>(`/api/me/workouts/${sessionId}/exercises`, {
    method: 'POST',
    body: { exerciseId },
  })
}

export function updateSessionExercise(
  sessionId: string,
  sessionExerciseId: string,
  body: UpdateSessionExerciseRequest,
): Promise<SessionExercise> {
  return apiRequest<SessionExercise>(`/api/me/workouts/${sessionId}/exercises/${sessionExerciseId}`, {
    method: 'PATCH',
    body,
  })
}

export function removeSessionExercise(sessionId: string, sessionExerciseId: string): Promise<void> {
  return apiRequest<void>(`/api/me/workouts/${sessionId}/exercises/${sessionExerciseId}`, {
    method: 'DELETE',
  })
}

export function reorderSessionExercises(
  sessionId: string,
  exerciseIds: string[],
): Promise<SessionExercise[]> {
  return apiRequest<SessionExercise[]>(`/api/me/workouts/${sessionId}/exercise-order`, {
    method: 'PUT',
    body: { exerciseIds },
  })
}

export function addSet(
  sessionId: string,
  sessionExerciseId: string,
  body: AddSetRequest = {},
): Promise<WorkoutSet> {
  return apiRequest<WorkoutSet>(`/api/me/workouts/${sessionId}/exercises/${sessionExerciseId}/sets`, {
    method: 'POST',
    body,
  })
}

export function updateSet(
  sessionId: string,
  setId: string,
  body: UpdateSetRequest,
): Promise<WorkoutSet> {
  return apiRequest<WorkoutSet>(`/api/me/workouts/${sessionId}/sets/${setId}`, {
    method: 'PATCH',
    body,
  })
}

export function removeSet(sessionId: string, setId: string): Promise<void> {
  return apiRequest<void>(`/api/me/workouts/${sessionId}/sets/${setId}`, {
    method: 'DELETE',
  })
}

export function fetchAssignments(params: {
  state?: AssignmentState
  cursor?: string | null
  pageSize?: number
} = {}): Promise<AssignmentListResponse> {
  const search = new URLSearchParams()
  search.set('pageSize', String(params.pageSize ?? 20))
  if (params.state) {
    search.set('state', params.state)
  }
  if (params.cursor) {
    search.set('cursor', params.cursor)
  }
  return apiRequest<AssignmentListResponse>(`/api/me/workout-assignments?${search.toString()}`)
}

export function fetchAssignment(assignmentId: string): Promise<AssignmentListItem> {
  return apiRequest<AssignmentListItem>(`/api/me/workout-assignments/${assignmentId}`)
}
