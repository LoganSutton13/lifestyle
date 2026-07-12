import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { countCompletedSets, countExercisesWithSets, countIncompleteSets, formatClock } from './utils'
import type { WorkoutSession } from './types'

export interface EndWorkoutSheetProps {
  open: boolean
  onClose: () => void
  session: WorkoutSession
  elapsedSeconds: number
  submitting?: boolean
  onConfirm: (payload: { discardIncompleteSets: boolean; notes?: string }) => void
}

export function EndWorkoutSheet({
  open,
  onClose,
  session,
  elapsedSeconds,
  submitting,
  onConfirm,
}: EndWorkoutSheetProps) {
  const [notes, setNotes] = useState(session.notes)
  const completedExercises = countExercisesWithSets(session.exercises)
  const completedSets = countCompletedSets(session.exercises)
  const incompleteSets = countIncompleteSets(session.exercises)

  if (!open) {
    return null
  }

  return (
    <Modal open={open} onClose={onClose} title="End Workout">
      <div className="flex flex-col gap-4">
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-textMuted">Duration</dt>
            <dd className="text-lg font-semibold text-text">{formatClock(elapsedSeconds)}</dd>
          </div>
          <div>
            <dt className="text-textMuted">Exercises</dt>
            <dd className="text-lg font-semibold text-text">{completedExercises}</dd>
          </div>
          <div>
            <dt className="text-textMuted">Completed sets</dt>
            <dd className="text-lg font-semibold text-text">{completedSets}</dd>
          </div>
          <div>
            <dt className="text-textMuted">Incomplete sets</dt>
            <dd className="text-lg font-semibold text-text">{incompleteSets}</dd>
          </div>
        </dl>

        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-text">Workout note (optional)</span>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={3}
            className="min-h-touch w-full rounded-xl border border-border bg-background px-3 py-2.5 text-base text-text outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </label>

        {incompleteSets > 0 ? (
          <div className="flex flex-col gap-3 rounded-xl bg-warning/10 p-3">
            <p className="flex items-start gap-2 text-sm text-text">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
              This workout contains incomplete sets. They will not be included in workout history.
            </p>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button variant="secondary" className="flex-1" onClick={onClose}>
                Review Sets
              </Button>
              <Button
                variant="danger"
                className="flex-1"
                loading={submitting}
                disabled={completedSets === 0}
                onClick={() => onConfirm({ discardIncompleteSets: true, notes })}
              >
                Discard Incomplete Sets and Finish
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={onClose}>
              Cancel
            </Button>
            <Button
              className="flex-1"
              loading={submitting}
              disabled={completedSets === 0}
              onClick={() => onConfirm({ discardIncompleteSets: true, notes })}
            >
              Complete Workout
            </Button>
          </div>
        )}
        {completedSets === 0 ? (
          <p className="text-sm text-danger">Complete at least one set before ending this workout.</p>
        ) : null}
      </div>
    </Modal>
  )
}
