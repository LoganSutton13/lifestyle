import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Dumbbell } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { PageTitle } from '../../components/ui/PageTitle'
import { Spinner } from '../../components/ui/Spinner'
import { getErrorMessage } from '../../lib/errors'
import * as workoutsApi from './api'
import {
  formatDurationSeconds,
  formatLoadDisplay,
  sessionDisplayTitle,
  sortedExercises,
} from './helpers'
import { workoutKeys } from './queryKeys'
import type { SessionExercise, WorkoutSet } from './types'

function SetReadOnlyRow({ set, trackingType }: { set: WorkoutSet; trackingType: string }) {
  const parts: string[] = [`#${set.position + 1}`, set.setType]
  if (trackingType === 'reps_load' || trackingType === 'reps_only') {
    if (set.loadValue != null) {
      parts.push(`${formatLoadDisplay(set.loadValue)} ${set.loadUnitKey ?? ''}`.trim())
    }
    if (set.reps != null) {
      parts.push(`${set.reps} reps`)
    }
  }
  if (trackingType === 'duration' && set.durationSeconds != null) {
    parts.push(`${set.durationSeconds}s`)
  }
  return (
    <li className="flex items-center justify-between gap-2 border-b border-border py-2 text-sm last:border-b-0">
      <span className="text-text">{parts.join(' · ')}</span>
      {set.completedAt ? (
        <span className="text-xs font-medium text-primaryDark">Done</span>
      ) : (
        <span className="text-xs text-textMuted">Incomplete</span>
      )}
    </li>
  )
}

function ExerciseReadOnly({ exercise }: { exercise: SessionExercise }) {
  return (
    <Card className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold text-text">{exercise.exercise.name}</h2>
        <p className="text-sm text-textMuted">
          {exercise.exercise.equipment.displayName}
          {exercise.isUnilateral ? ' · Per side' : ''}
        </p>
      </div>
      {exercise.prescription ? (
        <div className="rounded-xl bg-surface px-3 py-2 text-sm text-textMuted">
          <p className="font-medium text-text">Prescription</p>
          {exercise.prescription.notes ? <p>{exercise.prescription.notes}</p> : null}
          <ul className="mt-1 space-y-1">
            {exercise.prescription.sets.map((set) => (
              <li key={set.id}>
                Set {set.position + 1}:{' '}
                {set.targetLoadValue
                  ? `${formatLoadDisplay(set.targetLoadValue)} ${set.targetLoadUnitKey ?? ''} × `
                  : ''}
                {set.targetRepsMin != null || set.targetRepsMax != null
                  ? `${set.targetRepsMin ?? '?'}${
                      set.targetRepsMax != null && set.targetRepsMax !== set.targetRepsMin
                        ? `–${set.targetRepsMax}`
                        : ''
                    } reps`
                  : ''}
                {set.targetDurationSeconds != null ? `${set.targetDurationSeconds}s` : ''}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <ul>
        {[...exercise.sets]
          .sort((a, b) => a.position - b.position)
          .map((set) => (
            <SetReadOnlyRow key={set.id} set={set} trackingType={exercise.exercise.trackingType} />
          ))}
      </ul>
    </Card>
  )
}

export function WorkoutHistoryDetailPage() {
  const { sessionId = '' } = useParams()

  const query = useQuery({
    queryKey: workoutKeys.detail(sessionId),
    queryFn: () => workoutsApi.fetchWorkoutSession(sessionId),
    enabled: Boolean(sessionId),
  })

  if (query.isLoading) {
    return <Spinner label="Loading workout..." />
  }

  if (query.isError || !query.data) {
    return (
      <EmptyState
        icon={<Dumbbell className="h-8 w-8" />}
        title="Workout not found"
        description={query.error ? getErrorMessage(query.error) : 'This session could not be loaded.'}
        action={
          <Link to="/app/workouts">
            <Button variant="secondary">Back to workouts</Button>
          </Link>
        }
      />
    )
  }

  const session = query.data
  const durationSeconds = session.completedAt
    ? Math.max(
        0,
        Math.floor((new Date(session.completedAt).getTime() - new Date(session.startedAt).getTime()) / 1000),
      )
    : 0

  return (
    <div className="space-y-5">
      <Link
        to="/app/workouts"
        className="inline-flex min-h-touch items-center gap-2 text-sm font-medium text-primary hover:text-primaryDark"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to workouts
      </Link>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-textMuted">Completed workout</p>
        <PageTitle>{sessionDisplayTitle(session)}</PageTitle>
        <p className="text-sm text-textMuted">
          {session.source === 'assigned' ? 'Assigned' : 'Freestyle'} ·{' '}
          {session.completedAt ? new Date(session.completedAt).toLocaleString() : '—'} ·{' '}
          {formatDurationSeconds(durationSeconds || Math.floor((Date.now() - new Date(session.startedAt).getTime()) / 1000))}
        </p>
        {session.notes ? <p className="mt-2 text-sm text-text">{session.notes}</p> : null}
      </div>

      {sortedExercises(session).map((exercise) => (
        <ExerciseReadOnly key={exercise.id} exercise={exercise} />
      ))}

      {session.exercises.length === 0 ? (
        <p className="text-sm text-textMuted">This workout has no exercises.</p>
      ) : null}
    </div>
  )
}
