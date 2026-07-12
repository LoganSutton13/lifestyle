import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import type { AssignmentListItem } from './types'

export interface AssignedWorkoutCardProps {
  assignment: AssignmentListItem
  disabled?: boolean
  loading?: boolean
  onStart: (assignmentId: string) => void
  onResume?: (sessionId: string) => void
}

export function AssignedWorkoutCard({
  assignment,
  disabled,
  loading,
  onStart,
  onResume,
}: AssignedWorkoutCardProps) {
  const canResume = assignment.state === 'in_progress' && assignment.sessionId

  return (
    <Card className="space-y-3">
      <div>
        <h3 className="text-lg font-semibold text-text">{assignment.title}</h3>
        <p className="text-sm text-textMuted">
          From {assignment.coachName} · {assignment.exerciseCount} exercise
          {assignment.exerciseCount === 1 ? '' : 's'}
        </p>
        {assignment.scheduledFor ? (
          <p className="text-sm text-textMuted">Scheduled {assignment.scheduledFor}</p>
        ) : null}
        {assignment.notes ? <p className="mt-1 text-sm text-text">{assignment.notes}</p> : null}
      </div>
      {canResume ? (
        <Button
          className="w-full"
          disabled={disabled}
          onClick={() => onResume?.(assignment.sessionId!)}
        >
          Resume
        </Button>
      ) : (
        <Button
          className="w-full"
          variant="secondary"
          disabled={disabled}
          loading={loading}
          onClick={() => onStart(assignment.id)}
        >
          Start assigned workout
        </Button>
      )}
    </Card>
  )
}
