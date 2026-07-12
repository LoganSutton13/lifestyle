import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/ui/EmptyState'
import { Spinner } from '../../components/ui/Spinner'
import { useToast } from '../../components/ui/Toast'
import { getErrorMessage } from '../../lib/errors'
import type { Exercise } from '../exercises/types'
import * as workoutsApi from './api'
import { AddExercisePage } from './AddExercisePage'
import { DiscardWorkoutDialog } from './DiscardWorkoutDialog'
import { EndWorkoutSheet } from './EndWorkoutSheet'
import { ExercisePage } from './ExercisePage'
import { ADD_EXERCISE_PAGE_KEY, ExercisePager, type ExercisePagerHandle } from './ExercisePager'
import { copySetValues, sessionDisplayTitle, sortedExercises } from './helpers'
import { workoutKeys } from './queryKeys'
import { RestTimer } from './RestTimer'
import type { SessionExercise, UpdateSetPayload, WorkoutSession, WorkoutSet } from './types'
import { formatClock, useElapsedSeconds } from './utils'

/** Owns the 1s tick so the rest of the active workout UI does not re-render every second. */
function WorkoutElapsedLabel({ startedAt }: { startedAt: string }) {
  const elapsedSeconds = useElapsedSeconds(startedAt)
  return <p className="text-sm tabular-nums text-textMuted">{formatClock(elapsedSeconds)}</p>
}

function patchSession(
  session: WorkoutSession | undefined,
  updater: (current: WorkoutSession) => WorkoutSession,
): WorkoutSession | undefined {
  return session ? updater(session) : session
}

function replaceExercise(session: WorkoutSession, next: SessionExercise): WorkoutSession {
  return {
    ...session,
    exercises: session.exercises.map((item) => (item.id === next.id ? next : item)),
  }
}

function replaceSet(session: WorkoutSession, sessionExerciseId: string, nextSet: WorkoutSet): WorkoutSession {
  return {
    ...session,
    exercises: session.exercises.map((exercise) =>
      exercise.id === sessionExerciseId
        ? { ...exercise, sets: exercise.sets.map((set) => (set.id === nextSet.id ? nextSet : set)) }
        : exercise,
    ),
  }
}

export function ActiveWorkoutPage() {
  const { sessionId = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const pagerRef = useRef<ExercisePagerHandle>(null)
  const [endOpen, setEndOpen] = useState(false)
  const [discardOpen, setDiscardOpen] = useState(false)
  const [addingExerciseId, setAddingExerciseId] = useState<string | null>(null)

  const query = useQuery({
    queryKey: workoutKeys.detail(sessionId),
    queryFn: () => workoutsApi.fetchWorkoutSession(sessionId),
    enabled: Boolean(sessionId),
  })

  const session = query.data
  const exercises = useMemo(() => (session ? sortedExercises(session) : []), [session])

  const exerciseParam = searchParams.get('exercise')
  const activeId = useMemo(() => {
    if (!session) return ADD_EXERCISE_PAGE_KEY
    if (exerciseParam === ADD_EXERCISE_PAGE_KEY) return ADD_EXERCISE_PAGE_KEY
    if (exerciseParam && exercises.some((item) => item.id === exerciseParam)) {
      return exerciseParam
    }
    return exercises[0]?.id ?? ADD_EXERCISE_PAGE_KEY
  }, [exerciseParam, exercises, session])

  useEffect(() => {
    if (!session) return
    const valid =
      exerciseParam === ADD_EXERCISE_PAGE_KEY ||
      (exerciseParam != null && exercises.some((item) => item.id === exerciseParam))
    if (!valid) {
      const fallback = exercises[0]?.id ?? ADD_EXERCISE_PAGE_KEY
      setSearchParams({ exercise: fallback }, { replace: true })
    }
  }, [exerciseParam, exercises, session, setSearchParams])

  const setActiveId = useCallback(
    (id: string) => {
      setSearchParams({ exercise: id }, { replace: true })
    },
    [setSearchParams],
  )

  const setSessionCache = (next: WorkoutSession) => {
    queryClient.setQueryData(workoutKeys.detail(sessionId), next)
    queryClient.setQueryData(workoutKeys.active(), { session: next })
  }

  const completeMutation = useMutation({
    mutationFn: (payload: { discardIncompleteSets: boolean; notes?: string }) =>
      workoutsApi.completeWorkout(sessionId, {
        discardIncompleteSets: payload.discardIncompleteSets,
        notes: payload.notes || null,
      }),
    onSuccess: async (completed) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: workoutKeys.active() }),
        queryClient.invalidateQueries({ queryKey: workoutKeys.history({}) }),
        queryClient.invalidateQueries({ queryKey: workoutKeys.assignments({}) }),
      ])
      queryClient.setQueryData(workoutKeys.detail(completed.id), completed)
      showToast('Workout completed')
      navigate(`/app/workouts/history/${completed.id}`)
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const discardMutation = useMutation({
    mutationFn: () => workoutsApi.discardWorkout(sessionId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: workoutKeys.active() }),
        queryClient.invalidateQueries({ queryKey: workoutKeys.assignments({}) }),
      ])
      queryClient.removeQueries({ queryKey: workoutKeys.detail(sessionId) })
      showToast('Workout discarded')
      navigate('/app/workouts')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const addExerciseMutation = useMutation({
    mutationFn: (exerciseId: string) => workoutsApi.addSessionExercise(sessionId, exerciseId),
    onMutate: (exerciseId) => setAddingExerciseId(exerciseId),
    onSuccess: (sessionExercise) => {
      queryClient.setQueryData<WorkoutSession>(workoutKeys.detail(sessionId), (current) =>
        patchSession(current, (sessionValue) => ({
          ...sessionValue,
          exercises: [...sessionValue.exercises, sessionExercise],
        })),
      )
      setActiveId(sessionExercise.id)
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
    onSettled: () => setAddingExerciseId(null),
  })

  if (query.isLoading) {
    return <Spinner label="Loading active workout..." />
  }

  if (query.isError || !session) {
    return (
      <EmptyState
        title="Workout unavailable"
        description={query.error ? getErrorMessage(query.error) : 'Session not found.'}
        action={
          <Link to="/app/workouts">
            <Button variant="secondary">Back to workouts</Button>
          </Link>
        }
      />
    )
  }

  if (session.status !== 'in_progress') {
    navigate(`/app/workouts/history/${session.id}`, { replace: true })
    return <Spinner label="Opening history..." />
  }

  const existingExerciseIds = exercises.map((item) => item.exercise.id)
  const currentExercise = exercises.find((item) => item.id === activeId)
  const restDefault = currentExercise?.restSeconds ?? 90

  const handleSelectExercise = (exercise: Exercise) => {
    addExerciseMutation.mutate(exercise.id)
  }

  const handleSaveSet = async (
    sessionExerciseId: string,
    setId: string,
    payload: UpdateSetPayload,
  ): Promise<WorkoutSet> => {
    const updated = await workoutsApi.updateSet(sessionId, sessionExerciseId, setId, payload)
    queryClient.setQueryData<WorkoutSession>(workoutKeys.detail(sessionId), (current) =>
      patchSession(current, (sessionValue) => replaceSet(sessionValue, sessionExerciseId, updated)),
    )
    return updated
  }

  const handleAddSet = async (exercise: SessionExercise, setType: 'normal' | 'drop' = 'normal') => {
    const last = [...exercise.sets].sort((a, b) => a.position - b.position).at(-1)
    const copied = copySetValues(last)
    try {
      const created = await workoutsApi.addSet(sessionId, exercise.id, {
        setType,
        ...copied,
      })
      queryClient.setQueryData<WorkoutSession>(workoutKeys.detail(sessionId), (current) =>
        patchSession(current, (sessionValue) =>
          replaceExercise(sessionValue, {
            ...exercise,
            sets: [...exercise.sets, created],
          }),
        ),
      )
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  }

  const handleDeleteSet = async (exercise: SessionExercise, setId: string) => {
    try {
      await workoutsApi.removeSet(sessionId, exercise.id, setId)
      queryClient.setQueryData<WorkoutSession>(workoutKeys.detail(sessionId), (current) =>
        patchSession(current, (sessionValue) =>
          replaceExercise(sessionValue, {
            ...exercise,
            sets: exercise.sets.filter((set) => set.id !== setId),
          }),
        ),
      )
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  }

  const handleRemoveLastSet = async (exercise: SessionExercise) => {
    const last = [...exercise.sets].sort((a, b) => a.position - b.position).at(-1)
    if (!last) return
    const hasData =
      last.completedAt || last.reps != null || last.loadValue != null || last.durationSeconds != null
    if (hasData && !window.confirm('Remove the last set? It has data.')) return
    await handleDeleteSet(exercise, last.id)
  }

  const handleToggleUnilateral = async (exercise: SessionExercise, value: boolean) => {
    try {
      const updated = await workoutsApi.updateSessionExercise(sessionId, exercise.id, {
        isUnilateral: value,
      })
      queryClient.setQueryData<WorkoutSession>(workoutKeys.detail(sessionId), (current) =>
        patchSession(current, (sessionValue) => replaceExercise(sessionValue, updated)),
      )
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  }

  const handleReorder = async (exercise: SessionExercise, direction: 'left' | 'right') => {
    const ordered = sortedExercises(session)
    const index = ordered.findIndex((item) => item.id === exercise.id)
    const swapWith = direction === 'left' ? index - 1 : index + 1
    if (index < 0 || swapWith < 0 || swapWith >= ordered.length) return
    const nextOrder = [...ordered]
    ;[nextOrder[index], nextOrder[swapWith]] = [nextOrder[swapWith]!, nextOrder[index]!]
    try {
      const exercisesResult = await workoutsApi.reorderSessionExercises(
        sessionId,
        nextOrder.map((item) => item.id),
      )
      setSessionCache({ ...session, exercises: exercisesResult })
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  }

  const handleRemoveExercise = async (exercise: SessionExercise, index: number) => {
    const hasData = exercise.sets.some(
      (set) =>
        set.completedAt !== null ||
        set.reps !== null ||
        set.loadValue !== null ||
        set.durationSeconds !== null,
    )
    if (hasData && !window.confirm('Remove this exercise and all of its sets from the workout?')) {
      return
    }
    try {
      await workoutsApi.removeSessionExercise(sessionId, exercise.id)
      const remaining = exercises.filter((item) => item.id !== exercise.id)
      setSessionCache({
        ...session,
        exercises: remaining,
      })
      const next = remaining[index - 1]?.id ?? remaining[index]?.id ?? ADD_EXERCISE_PAGE_KEY
      setActiveId(next)
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  }

  const pages = [
    ...exercises.map((exercise, index) => ({
      id: exercise.id,
      label: exercise.exercise.name,
      content: (
        <div className="h-full overflow-y-auto px-4 py-4">
          <ExercisePage
            sessionExercise={exercise}
            canMoveLeft={index > 0}
            canMoveRight={index < exercises.length - 1}
            onMoveLeft={() => void handleReorder(exercise, 'left')}
            onMoveRight={() => void handleReorder(exercise, 'right')}
            onRemove={() => void handleRemoveExercise(exercise, index)}
            onToggleUnilateral={(value) => void handleToggleUnilateral(exercise, value)}
            onAddSet={() => void handleAddSet(exercise, 'normal')}
            onDropSet={() => void handleAddSet(exercise, 'drop')}
            onRemoveLastSet={() => void handleRemoveLastSet(exercise)}
            onDeleteSet={(setId) => void handleDeleteSet(exercise, setId)}
            onSaveSet={(setId, payload) => handleSaveSet(exercise.id, setId, payload)}
          />
        </div>
      ),
    })),
    {
      id: ADD_EXERCISE_PAGE_KEY,
      label: 'Add exercise',
      content: (
        <AddExercisePage
          sessionId={session.id}
          existingExerciseIds={existingExerciseIds}
          addingExerciseId={addingExerciseId}
          onSelectExercise={handleSelectExercise}
        />
      ),
    },
  ]

  return (
    <div className="fixed inset-x-0 bottom-[calc(4.5rem+env(safe-area-inset-bottom))] top-0 z-30 flex flex-col bg-background sm:static sm:inset-auto sm:z-auto sm:min-h-[70vh]">
      <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-border bg-background px-4 py-3">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-bold text-text">{sessionDisplayTitle(session)}</h1>
          <WorkoutElapsedLabel startedAt={session.startedAt} />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button size="sm" variant="ghost" aria-label="Discard workout" onClick={() => setDiscardOpen(true)}>
            <X className="h-5 w-5" />
          </Button>
          <Button size="sm" onClick={() => setEndOpen(true)}>
            End Workout
          </Button>
        </div>
      </header>

      <ExercisePager
        ref={pagerRef}
        pages={pages}
        activeId={activeId}
        onActiveChange={setActiveId}
      />

      <div className="border-t border-border px-4 py-2">
        <RestTimer sessionId={session.id} defaultDurationSeconds={restDefault} />
      </div>

      <EndWorkoutSheet
        open={endOpen}
        session={session}
        submitting={completeMutation.isPending}
        onClose={() => setEndOpen(false)}
        onConfirm={(payload) => completeMutation.mutate(payload)}
      />

      <DiscardWorkoutDialog
        open={discardOpen}
        submitting={discardMutation.isPending}
        onClose={() => setDiscardOpen(false)}
        onConfirm={() => discardMutation.mutate()}
      />
    </div>
  )
}
