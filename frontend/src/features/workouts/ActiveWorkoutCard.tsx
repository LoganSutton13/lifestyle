import { Link } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import {
  countCompletedSets,
  countExercisesWithSets,
  formatElapsed,
  sessionDisplayTitle,
} from './helpers'
import type { WorkoutSession } from './types'

export interface ActiveWorkoutCardProps {
  session: WorkoutSession
  nowMs?: number
}

export function ActiveWorkoutCard({ session, nowMs }: ActiveWorkoutCardProps) {
  const exerciseCount = countExercisesWithSets(session)
  const completedSets = countCompletedSets(session)

  return (
    <Card className="space-y-4 border-primary/30 bg-primarySoft/40">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-primaryDark">Active workout</p>
        <h2 className="mt-1 text-xl font-bold text-text">{sessionDisplayTitle(session)}</h2>
        <p className="text-sm text-textMuted">
          {session.source === 'assigned' ? 'Assigned' : 'Freestyle'} · {formatElapsed(session.startedAt, nowMs)}
        </p>
        <p className="mt-1 text-sm text-textMuted">
          {exerciseCount} exercise{exerciseCount === 1 ? '' : 's'} with sets · {completedSets} completed set
          {completedSets === 1 ? '' : 's'}
        </p>
      </div>
      <Link to={`/app/workouts/active/${session.id}`}>
        <Button className="w-full">Resume Workout</Button>
      </Link>
    </Card>
  )
}
