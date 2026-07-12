export const coachWorkoutKeys = {
  all: ['coach-workouts'] as const,
  templates: (includeArchived = false) =>
    [...coachWorkoutKeys.all, 'templates', { includeArchived }] as const,
  template: (templateId: string) => [...coachWorkoutKeys.all, 'template', templateId] as const,
  clientAssignments: (clientId: string) =>
    [...coachWorkoutKeys.all, 'client-assignments', clientId] as const,
  clientHistory: (clientId: string, params: { cursor?: string | null; pageSize?: number } = {}) =>
    [...coachWorkoutKeys.all, 'client-history', clientId, params] as const,
  clientSession: (clientId: string, sessionId: string) =>
    [...coachWorkoutKeys.all, 'client-session', clientId, sessionId] as const,
}
