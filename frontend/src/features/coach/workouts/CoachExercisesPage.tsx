import { useEffect, useState } from 'react'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Dumbbell, Plus } from 'lucide-react'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { EmptyState } from '../../../components/ui/EmptyState'
import { Modal } from '../../../components/ui/Modal'
import { PageTitle } from '../../../components/ui/PageTitle'
import { Spinner } from '../../../components/ui/Spinner'
import { useToast } from '../../../components/ui/Toast'
import { getErrorMessage } from '../../../lib/errors'
import { useAuthUser } from '../../auth/hooks'
import { CreateExerciseForm } from '../../exercises/CreateExerciseForm'
import * as exercisesApi from '../../exercises/api'
import { ExerciseSearchFilters } from '../../exercises/ExerciseSearchFilters'
import { exerciseKeys } from '../../exercises/queryKeys'
import { trackingTypeLabel, type Exercise } from '../../exercises/types'

const SEARCH_DEBOUNCE_MS = 250

export function CoachExercisesPage() {
  const user = useAuthUser()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [queryInput, setQueryInput] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [equipment, setEquipment] = useState('')
  const [muscleGroup, setMuscleGroup] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<Exercise | null>(null)

  useEffect(() => {
    const handle = window.setTimeout(() => setDebouncedQuery(queryInput.trim()), SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(handle)
  }, [queryInput])

  const params = { query: debouncedQuery, equipment, muscleGroup }

  const searchQuery = useInfiniteQuery({
    queryKey: exerciseKeys.search(params),
    queryFn: ({ pageParam }) =>
      exercisesApi.searchExercises({ ...params, cursor: pageParam ?? undefined, pageSize: 30 }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  })

  const createMutation = useMutation({
    mutationFn: exercisesApi.createExercise,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: exerciseKeys.all })
      setCreateOpen(false)
      showToast('Exercise created')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string
      body: Parameters<typeof exercisesApi.updateExercise>[1]
    }) => exercisesApi.updateExercise(id, body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: exerciseKeys.all })
      setEditing(null)
      showToast('Exercise updated')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const archiveMutation = useMutation({
    mutationFn: exercisesApi.archiveExercise,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: exerciseKeys.all })
      showToast('Exercise archived')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const items = searchQuery.data?.pages.flatMap((page) => page.items) ?? []

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <PageTitle>Exercise library</PageTitle>
          <p className="text-sm text-textMuted">Create and manage global exercises</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          New exercise
        </Button>
      </div>

      <ExerciseSearchFilters
        query={queryInput}
        equipment={equipment}
        muscleGroup={muscleGroup}
        onQueryChange={setQueryInput}
        onEquipmentChange={setEquipment}
        onMuscleGroupChange={setMuscleGroup}
      />

      {searchQuery.isLoading ? <Spinner label="Loading exercises..." /> : null}

      {!searchQuery.isLoading && items.length === 0 ? (
        <EmptyState
          icon={<Dumbbell className="h-8 w-8" />}
          title="No exercises found"
          description="Try a different search or create a new exercise."
        />
      ) : null}

      <div className="space-y-3">
        {items.map((exercise) => {
          const isOwner = user?.id === exercise.createdByUserId
          return (
            <Card key={exercise.id} className="space-y-2">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-text">{exercise.name}</h2>
                  <p className="text-sm text-textMuted">
                    {exercise.equipment.displayName} · {trackingTypeLabel(exercise.trackingType)}
                  </p>
                  <p className="text-xs text-textMuted">
                    {exercise.primaryMuscles.map((m) => m.displayName).join(', ')}
                  </p>
                </div>
                {isOwner ? (
                  <div className="flex gap-2">
                    <Button size="sm" variant="secondary" onClick={() => setEditing(exercise)}>
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      loading={archiveMutation.isPending}
                      onClick={() => {
                        if (window.confirm(`Archive ${exercise.name}?`)) {
                          archiveMutation.mutate(exercise.id)
                        }
                      }}
                    >
                      Archive
                    </Button>
                  </div>
                ) : (
                  <span className="text-xs text-textMuted">Catalog exercise</span>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {searchQuery.hasNextPage ? (
        <Button
          variant="secondary"
          className="w-full"
          loading={searchQuery.isFetchingNextPage}
          onClick={() => void searchQuery.fetchNextPage()}
        >
          Load more
        </Button>
      ) : null}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create exercise">
        <CreateExerciseForm
          saving={createMutation.isPending}
          submitLabel="Create exercise"
          onCancel={() => setCreateOpen(false)}
          onSubmit={(values) => createMutation.mutate(values)}
        />
      </Modal>

      <Modal open={Boolean(editing)} onClose={() => setEditing(null)} title="Edit exercise">
        {editing ? (
          <CreateExerciseForm
            initial={editing}
            saving={updateMutation.isPending}
            submitLabel="Save changes"
            lockIdentityFields
            onCancel={() => setEditing(null)}
            onSubmit={(values) =>
              updateMutation.mutate({
                id: editing.id,
                body: {
                  name: values.name,
                  defaultUnilateral: values.defaultUnilateral,
                  defaultRestSeconds: values.defaultRestSeconds,
                  primaryMuscleKeys: values.primaryMuscleKeys,
                  secondaryMuscleKeys: values.secondaryMuscleKeys,
                  instructions: values.instructions,
                },
              })
            }
          />
        ) : null}
      </Modal>
    </div>
  )
}
