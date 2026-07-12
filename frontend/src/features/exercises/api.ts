import { apiRequest } from '../../lib/apiClient'
import type {
  Exercise,
  ExerciseCreateRequest,
  ExerciseListResponse,
  ExerciseSearchParams,
  ExerciseSuggestionsResponse,
  ExerciseUpdateRequest,
} from './types'

export function searchExercises(params: ExerciseSearchParams = {}): Promise<ExerciseListResponse> {
  const search = new URLSearchParams()
  if (params.query) {
    search.set('query', params.query)
  }
  if (params.equipment) {
    search.set('equipment', params.equipment)
  }
  if (params.muscleGroup) {
    search.set('muscleGroup', params.muscleGroup)
  }
  if (params.includeArchived) {
    search.set('includeArchived', 'true')
  }
  search.set('pageSize', String(params.pageSize ?? 30))
  if (params.cursor) {
    search.set('cursor', params.cursor)
  }
  return apiRequest<ExerciseListResponse>(`/api/exercises?${search.toString()}`)
}

export function fetchExerciseSuggestions(
  sessionId: string,
  limit = 3,
): Promise<ExerciseSuggestionsResponse> {
  const search = new URLSearchParams({ sessionId, limit: String(limit) })
  return apiRequest<ExerciseSuggestionsResponse>(`/api/me/exercises/suggestions?${search.toString()}`)
}

export function createExercise(body: ExerciseCreateRequest): Promise<Exercise> {
  return apiRequest<Exercise>('/api/exercises', {
    method: 'POST',
    body,
  })
}

export function updateExercise(exerciseId: string, body: ExerciseUpdateRequest): Promise<Exercise> {
  return apiRequest<Exercise>(`/api/exercises/${exerciseId}`, {
    method: 'PATCH',
    body,
  })
}

export function archiveExercise(exerciseId: string): Promise<Exercise> {
  return apiRequest<Exercise>(`/api/exercises/${exerciseId}`, {
    method: 'DELETE',
  })
}

export function restoreExercise(exerciseId: string): Promise<Exercise> {
  return apiRequest<Exercise>(`/api/exercises/${exerciseId}/restore`, {
    method: 'POST',
  })
}
