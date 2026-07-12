import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { fetchExerciseSuggestions } from '../exercises/api'
import { ExercisePickerSheet } from '../exercises/ExercisePickerSheet'
import { exerciseKeys } from '../exercises/queryKeys'
import type { Exercise } from '../exercises/types'

export interface AddExercisePageProps {
  sessionId: string
  existingExerciseIds: string[]
  onSelectExercise: (exercise: Exercise) => void
  addingExerciseId?: string | null
}

export function AddExercisePage({
  sessionId,
  existingExerciseIds,
  onSelectExercise,
  addingExerciseId,
}: AddExercisePageProps) {
  const [pickerOpen, setPickerOpen] = useState(false)

  const suggestionsQuery = useQuery({
    queryKey: exerciseKeys.suggestions(sessionId),
    queryFn: () => fetchExerciseSuggestions(sessionId, 3),
  })

  const suggestions = (suggestionsQuery.data?.items ?? []).filter(
    (item) => !existingExerciseIds.includes(item.id),
  )

  function handleSelect(exercise: Exercise) {
    onSelectExercise(exercise)
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-4 py-10 text-center">
      <button
        type="button"
        aria-label="Add an exercise"
        onClick={() => setPickerOpen(true)}
        className="flex h-20 w-20 items-center justify-center rounded-full bg-primary text-white shadow-lg transition-transform hover:scale-105"
      >
        <Plus className="h-10 w-10" />
      </button>

      <div>
        <h2 className="text-xl font-bold text-text">Add an exercise</h2>
        <p className="mt-1 text-sm text-textMuted">
          Search the exercise library or choose a suggestion.
        </p>
      </div>

      {suggestions.length > 0 ? (
        <div className="flex w-full max-w-sm flex-col gap-2">
          {suggestions.map((exercise) => {
            const isAdding = addingExerciseId === exercise.id
            return (
              <button
                key={exercise.id}
                type="button"
                disabled={isAdding}
                onClick={() => handleSelect(exercise)}
                className="flex min-h-touch w-full items-center justify-between gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-left transition-colors hover:border-primary disabled:opacity-60"
              >
                <span className="font-medium text-text">{exercise.name}</span>
                <span className="text-xs text-textMuted">
                  {isAdding ? 'Adding...' : exercise.equipment.displayName}
                </span>
              </button>
            )
          })}
        </div>
      ) : null}

      <Button variant="secondary" onClick={() => setPickerOpen(true)}>
        Browse All Exercises
      </Button>

      <ExercisePickerSheet
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        existingExerciseIds={existingExerciseIds}
        addingExerciseId={addingExerciseId}
        onSelect={handleSelect}
      />
    </div>
  )
}
