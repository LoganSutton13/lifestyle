import type { TrackingType } from '../exercises/types'
import type { SessionExercise, WorkoutSession, WorkoutSet } from './types'

export function formatElapsed(startedAt: string, nowMs = Date.now()): string {
  const elapsedMs = Math.max(0, nowMs - new Date(startedAt).getTime())
  const totalSeconds = Math.floor(elapsedMs / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

export function formatDurationSeconds(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${seconds}s`
}

export function sessionDisplayTitle(session: WorkoutSession): string {
  if (session.title?.trim()) {
    return session.title.trim()
  }
  return session.source === 'assigned' ? 'Assigned workout' : 'Freestyle'
}

export function countExercisesWithSets(session: WorkoutSession): number {
  return session.exercises.filter((exercise) => exercise.sets.length > 0).length
}

export function countCompletedSets(session: WorkoutSession): number {
  return session.exercises.reduce(
    (total, exercise) => total + exercise.sets.filter((set) => set.completedAt).length,
    0,
  )
}

export function countIncompleteSets(session: WorkoutSession): number {
  return session.exercises.reduce(
    (total, exercise) => total + exercise.sets.filter((set) => !set.completedAt).length,
    0,
  )
}

export function sortedExercises(session: WorkoutSession): SessionExercise[] {
  return [...session.exercises].sort((a, b) => a.position - b.position)
}

export interface SetFieldErrors {
  reps?: string
  loadValue?: string
  durationSeconds?: string
}

export function validateSetForCompletion(
  trackingType: TrackingType,
  set: Pick<WorkoutSet, 'reps' | 'loadValue' | 'loadUnitKey' | 'durationSeconds'>,
): SetFieldErrors {
  const errors: SetFieldErrors = {}

  if (trackingType === 'reps_load') {
    if (set.reps == null || set.reps < 0) {
      errors.reps = 'Reps are required'
    }
    if (set.loadValue == null || set.loadValue === '') {
      errors.loadValue = 'Load is required'
    } else if (!set.loadUnitKey) {
      errors.loadValue = 'Unit is required'
    }
  } else if (trackingType === 'reps_only') {
    if (set.reps == null || set.reps < 0) {
      errors.reps = 'Reps are required'
    }
  } else if (trackingType === 'duration') {
    if (set.durationSeconds == null || set.durationSeconds < 0) {
      errors.durationSeconds = 'Duration is required'
    }
  }

  return errors
}

export function hasSetFieldErrors(errors: SetFieldErrors): boolean {
  return Object.keys(errors).length > 0
}

export function copySetValues(set: WorkoutSet | undefined): {
  reps: number | null
  loadValue: string | null
  loadUnitKey: string | null
  durationSeconds: number | null
  rpe: string | null
} {
  if (!set) {
    return {
      reps: null,
      loadValue: null,
      loadUnitKey: 'lb',
      durationSeconds: null,
      rpe: null,
    }
  }
  return {
    reps: set.reps,
    loadValue: set.loadValue,
    loadUnitKey: set.loadUnitKey ?? 'lb',
    durationSeconds: set.durationSeconds,
    rpe: set.rpe,
  }
}

export function formatLoadDisplay(value: string | null | undefined): string {
  if (value == null || value === '') return ''
  const trimmed = value.replace(/\.?0+$/, '')
  return trimmed === '' ? '0' : trimmed
}

export function parseOptionalInt(raw: string): number | null {
  const trimmed = raw.trim()
  if (trimmed === '') return null
  const parsed = Number.parseInt(trimmed, 10)
  return Number.isFinite(parsed) ? parsed : null
}

export function parseOptionalDecimal(raw: string): string | null {
  const trimmed = raw.trim()
  if (trimmed === '') return null
  if (!/^\d+(\.\d+)?$/.test(trimmed)) return null
  return trimmed
}
