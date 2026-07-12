import { useEffect, useState } from 'react'

export function computeElapsedSeconds(startedAt: string, now: number = Date.now()): number {
  const started = new Date(startedAt).getTime()
  return Math.max(0, Math.floor((now - started) / 1000))
}

export function formatClock(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`
}

export function formatDurationCompact(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  if (minutes > 0) {
    return `${minutes}m`
  }
  return `${seconds}s`
}

/**
 * Ticks once per second based on wall-clock time so it recovers correctly
 * after the tab is backgrounded rather than drifting from a stale interval.
 */
export function useElapsedSeconds(startedAt: string | null | undefined): number {
  const [elapsed, setElapsed] = useState(() => (startedAt ? computeElapsedSeconds(startedAt) : 0))

  useEffect(() => {
    if (!startedAt) {
      setElapsed(0)
      return
    }

    const recalculate = () => setElapsed(computeElapsedSeconds(startedAt))
    recalculate()

    const interval = window.setInterval(recalculate, 1000)
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        recalculate()
      }
    }
    document.addEventListener('visibilitychange', handleVisibility)

    return () => {
      window.clearInterval(interval)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [startedAt])

  return elapsed
}

export function countExercisesWithSets(exercises: { sets: unknown[] }[]): number {
  return exercises.filter((exercise) => exercise.sets.length > 0).length
}

export function countCompletedSets(exercises: { sets: { completedAt: string | null }[] }[]): number {
  return exercises.reduce(
    (total, exercise) => total + exercise.sets.filter((set) => set.completedAt !== null).length,
    0,
  )
}

export function countIncompleteSets(exercises: { sets: { completedAt: string | null }[] }[]): number {
  return exercises.reduce(
    (total, exercise) => total + exercise.sets.filter((set) => set.completedAt === null).length,
    0,
  )
}
