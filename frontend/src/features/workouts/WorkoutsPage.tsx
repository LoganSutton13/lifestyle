import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Dumbbell } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { PageTitle } from '../../components/ui/PageTitle'
import { Spinner } from '../../components/ui/Spinner'
import { useToast } from '../../components/ui/Toast'
import { ApiError, getErrorMessage } from '../../lib/errors'
import * as workoutsApi from './api'
import { ActiveWorkoutCard } from './ActiveWorkoutCard'
import { AssignedWorkoutCard } from './AssignedWorkoutCard'
import { formatDurationSeconds } from './helpers'
import { workoutKeys } from './queryKeys'
import { StartFreestyleButton } from './StartFreestyleButton'

export function WorkoutsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [nowMs, setNowMs] = useState(() => Date.now())
  const [startingAssignmentId, setStartingAssignmentId] = useState<string | null>(null)

  useEffect(() => {
    const id = window.setInterval(() => setNowMs(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [])

  const activeQuery = useQuery({
    queryKey: workoutKeys.active(),
    queryFn: workoutsApi.fetchActiveWorkout,
  })

  const assignmentsQuery = useQuery({
    queryKey: workoutKeys.assignments({ state: 'available' }),
    queryFn: () => workoutsApi.fetchAssignments({ state: 'available', pageSize: 20 }),
  })

  const historyQuery = useInfiniteQuery({
    queryKey: workoutKeys.history({ pageSize: 20 }),
    queryFn: ({ pageParam }) =>
      workoutsApi.fetchWorkoutHistory({ cursor: pageParam ?? undefined, pageSize: 20 }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  })

  const startMutation = useMutation({
    mutationFn: workoutsApi.startWorkout,
    onSuccess: async (session) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: workoutKeys.active() }),
        queryClient.invalidateQueries({ queryKey: workoutKeys.assignments({}) }),
      ])
      queryClient.setQueryData(workoutKeys.detail(session.id), session)
      const ordered = [...session.exercises].sort((a, b) => a.position - b.position)
      const exerciseParam = session.source === 'freestyle' || ordered.length === 0 ? 'add' : ordered[0].id
      navigate(`/app/workouts/active/${session.id}?exercise=${exerciseParam}`)
    },
    onError: (error) => {
      if (error instanceof ApiError && error.code === 'ACTIVE_WORKOUT_EXISTS') {
        const sessionId = typeof error.details.sessionId === 'string' ? error.details.sessionId : null
        showToast('You already have an active workout', 'error')
        if (sessionId) {
          navigate(`/app/workouts/active/${sessionId}`)
        }
        return
      }
      showToast(getErrorMessage(error), 'error')
    },
    onSettled: () => setStartingAssignmentId(null),
  })

  const activeSession = activeQuery.data?.session ?? null
  const hasActive = Boolean(activeSession)
  const availableAssignments = assignmentsQuery.data?.items ?? []
  const historyItems = historyQuery.data?.pages.flatMap((page) => page.items) ?? []

  if (activeQuery.isLoading) {
    return <Spinner label="Loading workouts..." />
  }

  if (activeQuery.isError) {
    return (
      <EmptyState
        icon={<Dumbbell className="h-8 w-8" />}
        title="Could not load workouts"
        description={getErrorMessage(activeQuery.error)}
        action={
          <Button variant="secondary" onClick={() => void activeQuery.refetch()}>
            Retry
          </Button>
        }
      />
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <PageTitle>Workouts</PageTitle>
        <p className="text-sm text-textMuted">Track freestyle and assigned sessions</p>
      </div>

      {activeSession ? <ActiveWorkoutCard session={activeSession} nowMs={nowMs} /> : null}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-text">Assigned workouts</h2>
        {assignmentsQuery.isLoading ? <Spinner label="Loading assignments..." /> : null}
        {!assignmentsQuery.isLoading && availableAssignments.length === 0 ? (
          <p className="text-sm text-textMuted">No available assigned workouts.</p>
        ) : null}
        {availableAssignments.map((assignment) => (
          <AssignedWorkoutCard
            key={assignment.id}
            assignment={assignment}
            disabled={hasActive}
            loading={startMutation.isPending && startingAssignmentId === assignment.id}
            onStart={(assignmentId) => {
              setStartingAssignmentId(assignmentId)
              startMutation.mutate({ mode: 'assigned', assignmentId })
            }}
            onResume={(sessionId) => navigate(`/app/workouts/active/${sessionId}`)}
          />
        ))}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-text">Freestyle</h2>
        {hasActive ? (
          <p className="text-sm text-textMuted">Finish or discard your active workout before starting another.</p>
        ) : (
          <StartFreestyleButton
            loading={startMutation.isPending && startingAssignmentId === null}
            onStart={() => startMutation.mutate({ mode: 'freestyle' })}
          />
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-text">History</h2>
        {historyQuery.isLoading ? <Spinner label="Loading history..." /> : null}
        {!historyQuery.isLoading && historyItems.length === 0 ? (
          <EmptyState
            icon={<Dumbbell className="h-8 w-8" />}
            title="No completed workouts yet"
            description="Start a freestyle session or an assigned workout to begin tracking."
          />
        ) : null}
        {historyItems.map((item) => (
          <Link key={item.id} to={`/app/workouts/history/${item.id}`} className="block">
            <Card className="transition-colors hover:border-primary/40">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-text">
                    {item.title?.trim() || (item.source === 'assigned' ? 'Assigned workout' : 'Freestyle')}
                  </h3>
                  <p className="text-sm text-textMuted">
                    {new Date(item.completedAt).toLocaleString()} · {formatDurationSeconds(item.durationSeconds)}
                  </p>
                  <p className="text-sm text-textMuted">
                    {item.exerciseCount} exercises · {item.completedSetCount} sets
                  </p>
                </div>
                <span className="text-xs font-medium uppercase text-primaryDark">
                  {item.source === 'assigned' ? 'Assigned' : 'Freestyle'}
                </span>
              </div>
            </Card>
          </Link>
        ))}
        {historyQuery.hasNextPage ? (
          <Button
            variant="secondary"
            className="w-full"
            loading={historyQuery.isFetchingNextPage}
            onClick={() => void historyQuery.fetchNextPage()}
          >
            Load more
          </Button>
        ) : null}
      </section>
    </div>
  )
}
