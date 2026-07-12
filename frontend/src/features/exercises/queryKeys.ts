import type { ExerciseSearchParams } from './types'

export const exerciseKeys = {
  all: ['exercises'] as const,
  search: (params: ExerciseSearchParams) => [...exerciseKeys.all, 'search', params] as const,
  suggestions: (sessionId: string) => [...exerciseKeys.all, 'suggestions', sessionId] as const,
}
