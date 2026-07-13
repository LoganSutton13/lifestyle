import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useInfiniteQuery } from '@tanstack/react-query'
import { Dumbbell, X } from 'lucide-react'
import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/ui/EmptyState'
import { Spinner } from '../../components/ui/Spinner'
import { getErrorMessage } from '../../lib/errors'
import { searchExercises } from './api'
import { exerciseKeys } from './queryKeys'
import { ExerciseSearchFilters } from './ExerciseSearchFilters'
import { trackingTypeLabel, type Exercise } from './types'

export interface ExercisePickerSheetProps {
  open: boolean
  onClose: () => void
  existingExerciseIds: string[]
  onSelect: (exercise: Exercise) => void
  addingExerciseId?: string | null
}

const SEARCH_DEBOUNCE_MS = 250

export function ExercisePickerSheet({
  open,
  onClose,
  existingExerciseIds,
  onSelect,
  addingExerciseId,
}: ExercisePickerSheetProps) {
  const [queryInput, setQueryInput] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [equipment, setEquipment] = useState('')
  const [muscleGroup, setMuscleGroup] = useState('')
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  useEffect(() => {
    const handle = window.setTimeout(() => setDebouncedQuery(queryInput.trim()), SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(handle)
  }, [queryInput])

  useEffect(() => {
    if (!open) return

    previouslyFocused.current = document.activeElement as HTMLElement | null
    closeButtonRef.current?.focus()
    document.body.style.overflow = 'hidden'

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
      previouslyFocused.current?.focus()
    }
  }, [open, onClose])

  const params = { query: debouncedQuery, equipment, muscleGroup }

  const query = useInfiniteQuery({
    queryKey: exerciseKeys.search(params),
    queryFn: ({ pageParam }) =>
      searchExercises({ ...params, cursor: pageParam ?? undefined, pageSize: 30 }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    enabled: open,
  })

  if (!open || typeof document === 'undefined') {
    return null
  }

  const items = query.data?.pages.flatMap((page) => page.items) ?? []
  const existingSet = new Set(existingExerciseIds)

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex flex-col bg-background"
      role="dialog"
      aria-modal="true"
      aria-label="Browse exercises"
    >
      <div className="shrink-0 border-b border-border bg-background px-4 pb-3 pt-[calc(0.75rem+var(--safe-area-top))]">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-text">Add Exercise</h2>
          <button
            ref={closeButtonRef}
            type="button"
            aria-label="Close exercise picker"
            onClick={onClose}
            className="flex min-h-touch min-w-touch items-center justify-center rounded-full text-textMuted hover:bg-surface"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <ExerciseSearchFilters
          query={queryInput}
          equipment={equipment}
          muscleGroup={muscleGroup}
          onQueryChange={setQueryInput}
          onEquipmentChange={setEquipment}
          onMuscleGroupChange={setMuscleGroup}
        />
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3 pb-[calc(0.75rem+var(--safe-area-bottom))]">
        {query.isLoading ? <Spinner label="Searching exercises..." /> : null}

        {query.isError ? <Alert>{getErrorMessage(query.error)}</Alert> : null}

        {query.isSuccess && items.length === 0 ? (
          <EmptyState
            title="No exercises found"
            description="Try a different search term or filter."
            icon={<Dumbbell className="h-8 w-8" />}
          />
        ) : null}

        {items.length > 0 ? (
          <ul className="flex flex-col gap-2">
            {items.map((exercise) => {
              const alreadyAdded = existingSet.has(exercise.id)
              const isAdding = addingExerciseId === exercise.id
              return (
                <li key={exercise.id}>
                  <button
                    type="button"
                    onClick={() => onSelect(exercise)}
                    disabled={isAdding}
                    className="flex min-h-touch w-full flex-col items-start gap-1 rounded-xl border border-border bg-surface px-4 py-3 text-left transition-colors hover:border-primary disabled:opacity-60"
                  >
                    <div className="flex w-full items-center justify-between gap-2">
                      <span className="font-medium text-text">{exercise.name}</span>
                      {isAdding ? <span className="text-xs text-primary">Adding...</span> : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-textMuted">
                      <span>{exercise.equipment.displayName}</span>
                      <span aria-hidden="true">&middot;</span>
                      <span>
                        {exercise.primaryMuscles.map((m) => m.displayName).join(', ') || 'General'}
                      </span>
                      <span aria-hidden="true">&middot;</span>
                      <span>{trackingTypeLabel(exercise.trackingType)}</span>
                      {exercise.defaultUnilateral ? (
                        <>
                          <span aria-hidden="true">&middot;</span>
                          <span>Unilateral</span>
                        </>
                      ) : null}
                    </div>
                    {alreadyAdded ? (
                      <span className="mt-1 rounded-full bg-primarySoft px-2 py-0.5 text-xs font-medium text-primaryDark">
                        Already in workout
                      </span>
                    ) : null}
                  </button>
                </li>
              )
            })}
          </ul>
        ) : null}

        {query.hasNextPage ? (
          <div className="pt-3">
            <Button
              variant="secondary"
              className="w-full"
              loading={query.isFetchingNextPage}
              onClick={() => query.fetchNextPage()}
            >
              Load more
            </Button>
          </div>
        ) : null}
      </div>
    </div>,
    document.body,
  )
}
