import type { AssignmentState, CursorPageParams } from './types'

export const workoutKeys = {
  all: ['workouts'] as const,
  active: () => [...workoutKeys.all, 'active'] as const,
  detail: (sessionId: string) => [...workoutKeys.all, 'detail', sessionId] as const,
  history: (params: CursorPageParams = {}) => [...workoutKeys.all, 'history', params] as const,
  assignments: (params: { state?: AssignmentState; cursor?: string | null; pageSize?: number } = {}) =>
    [...workoutKeys.all, 'assignments', params] as const,
  assignment: (assignmentId: string) => [...workoutKeys.all, 'assignment', assignmentId] as const,
}
