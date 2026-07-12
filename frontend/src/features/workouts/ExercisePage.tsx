import { ExerciseHeader } from './ExerciseHeader'
import { SetActions } from './SetActions'
import { SetRow } from './SetRow'
import type { SessionExercise, UpdateSetPayload, WorkoutSet } from './types'

export interface ExercisePageProps {
  sessionExercise: SessionExercise
  canMoveLeft: boolean
  canMoveRight: boolean
  readOnly?: boolean
  onMoveLeft: () => void
  onMoveRight: () => void
  onRemove: () => void
  onToggleUnilateral: (value: boolean) => void
  onAddSet: () => void
  onDropSet: () => void
  onRemoveLastSet: () => void
  onDeleteSet: (setId: string) => void
  onSaveSet: (setId: string, payload: UpdateSetPayload) => Promise<WorkoutSet>
}

function summarizePrescription(sessionExercise: SessionExercise): string[] {
  const prescription = sessionExercise.prescription
  if (!prescription) return []

  const lines: string[] = []
  const firstSet = prescription.sets[0]
  if (firstSet) {
    const repsRange =
      firstSet.targetRepsMin !== null && firstSet.targetRepsMax !== null
        ? firstSet.targetRepsMin === firstSet.targetRepsMax
          ? `${firstSet.targetRepsMin} reps`
          : `${firstSet.targetRepsMin}\u2013${firstSet.targetRepsMax} reps`
        : firstSet.targetRepsMin !== null
          ? `${firstSet.targetRepsMin}+ reps`
          : null
    const loadPart = firstSet.targetLoadValue
      ? ` @ ${firstSet.targetLoadValue} ${firstSet.targetLoadUnitKey ?? ''}`.trim()
      : ''
    if (repsRange) {
      lines.push(`Target: ${prescription.sets.length} sets \u00d7 ${repsRange}${loadPart}`)
    } else if (firstSet.targetDurationSeconds) {
      lines.push(`Target: ${prescription.sets.length} sets \u00d7 ${firstSet.targetDurationSeconds} sec`)
    }
  }
  lines.push(`Rest: ${sessionExercise.restSeconds} sec`)
  if (prescription.notes) {
    lines.push(`Coach note: ${prescription.notes}`)
  }
  return lines
}

export function ExercisePage({
  sessionExercise,
  canMoveLeft,
  canMoveRight,
  readOnly,
  onMoveLeft,
  onMoveRight,
  onRemove,
  onToggleUnilateral,
  onAddSet,
  onDropSet,
  onRemoveLastSet,
  onDeleteSet,
  onSaveSet,
}: ExercisePageProps) {
  const prescriptionLines = summarizePrescription(sessionExercise)
  const sets = sessionExercise.sets

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto pb-4">
      <ExerciseHeader
        sessionExercise={sessionExercise}
        canMoveLeft={canMoveLeft}
        canMoveRight={canMoveRight}
        readOnly={readOnly}
        onMoveLeft={onMoveLeft}
        onMoveRight={onMoveRight}
        onRemove={onRemove}
        onToggleUnilateral={onToggleUnilateral}
      />

      {prescriptionLines.length > 0 ? (
        <div className="rounded-xl bg-primarySoft/50 px-4 py-3 text-sm text-primaryDark">
          {prescriptionLines.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
      ) : null}

      <div className="flex flex-col gap-2">
        {sets.map((set, idx) => (
          <SetRow
            key={set.id}
            set={set}
            index={idx + 1}
            trackingType={sessionExercise.exercise.trackingType}
            isUnilateral={sessionExercise.isUnilateral}
            isFinal={idx === sets.length - 1}
            readOnly={readOnly}
            onSave={(payload) => onSaveSet(set.id, payload)}
            onDelete={() => onDeleteSet(set.id)}
          />
        ))}

        {sets.length === 0 ? (
          <p className="rounded-xl border border-dashed border-border px-4 py-6 text-center text-sm text-textMuted">
            No sets yet. Add your first set below.
          </p>
        ) : null}
      </div>

      {!readOnly ? (
        <SetActions
          onAddSet={onAddSet}
          onDropSet={onDropSet}
          onRemoveSet={onRemoveLastSet}
          canRemove={sets.length > 0}
        />
      ) : null}
    </div>
  )
}
