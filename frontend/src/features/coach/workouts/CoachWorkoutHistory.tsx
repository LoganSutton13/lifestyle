import { useQuery } from '@tanstack/react-query'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { Spinner } from '../../../components/ui/Spinner'
import { getErrorMessage } from '../../../lib/errors'
import {
  formatDurationSeconds,
  formatLoadDisplay,
  sessionDisplayTitle,
  sortedExercises,
} from '../../workouts/helpers'
import type { SessionExercise, WorkoutSession } from '../../workouts/types'
import * as coachWorkoutsApi from './api'
import { coachWorkoutKeys } from './queryKeys'

function ExerciseComparison({ exercise }: { exercise: SessionExercise }) {
  return (
    <Card className="space-y-3">
      <div>
        <h3 className="font-semibold text-text">{exercise.exercise.name}</h3>
        <p className="text-sm text-textMuted">{exercise.exercise.equipment.displayName}</p>
      </div>
      {exercise.prescription ? (
        <div className="rounded-xl bg-surface px-3 py-2 text-sm">
          <p className="font-medium text-text">Prescribed</p>
          <ul className="mt-1 space-y-1 text-textMuted">
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
      <div className="text-sm">
        <p className="font-medium text-text">Performed</p>
        <ul className="mt-1 space-y-1 text-textMuted">
          {[...exercise.sets]
            .sort((a, b) => a.position - b.position)
            .map((set) => (
              <li key={set.id}>
                Set {set.position + 1}:{' '}
                {set.loadValue != null
                  ? `${formatLoadDisplay(set.loadValue)} ${set.loadUnitKey ?? ''} × `
                  : ''}
                {set.reps != null ? `${set.reps} reps` : ''}
                {set.durationSeconds != null ? `${set.durationSeconds}s` : ''}
                {set.completedAt ? ' ✓' : ''}
              </li>
            ))}
        </ul>
      </div>
    </Card>
  )
}

export function CoachWorkoutHistory({
  clientId,
  sessionId,
  onBack,
}: {
  clientId: string
  sessionId: string
  onBack: () => void
}) {
  const query = useQuery({
    queryKey: coachWorkoutKeys.clientSession(clientId, sessionId),
    queryFn: () => coachWorkoutsApi.fetchClientWorkoutDetail(clientId, sessionId),
  })

  if (query.isLoading) {
    return <Spinner label="Loading workout..." />
  }

  if (query.isError || !query.data) {
    return (
      <div className="space-y-3">
        <Button variant="secondary" onClick={onBack}>
          Back
        </Button>
        <p className="text-sm text-danger">
          {query.error ? getErrorMessage(query.error) : 'Workout not found'}
        </p>
      </div>
    )
  }

  const session: WorkoutSession = query.data
  const durationSeconds = session.completedAt
    ? Math.max(
        0,
        Math.floor(
          (new Date(session.completedAt).getTime() - new Date(session.startedAt).getTime()) / 1000,
        ),
      )
    : 0

  return (
    <div className="space-y-4">
      <Button variant="secondary" onClick={onBack}>
        Back to history
      </Button>
      <div>
        <h3 className="text-xl font-bold text-text">{sessionDisplayTitle(session)}</h3>
        <p className="text-sm text-textMuted">
          {session.source === 'assigned' ? 'Assigned' : 'Freestyle'} ·{' '}
          {session.completedAt ? new Date(session.completedAt).toLocaleString() : 'In progress'} ·{' '}
          {formatDurationSeconds(durationSeconds)}
        </p>
      </div>
      {sortedExercises(session).map((exercise) => (
        <ExerciseComparison key={exercise.id} exercise={exercise} />
      ))}
    </div>
  )
}
