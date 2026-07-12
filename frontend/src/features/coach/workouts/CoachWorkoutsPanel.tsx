import { useState } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { Spinner } from '../../../components/ui/Spinner'
import { useToast } from '../../../components/ui/Toast'
import { getErrorMessage } from '../../../lib/errors'
import { formatDurationSeconds } from '../../workouts/helpers'
import * as coachWorkoutsApi from './api'
import { CoachWorkoutHistory } from './CoachWorkoutHistory'
import { coachWorkoutKeys } from './queryKeys'
import { WorkoutAssignmentForm } from './WorkoutAssignmentForm'

export function CoachWorkoutsPanel({ clientId }: { clientId: string }) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)

  const assignmentsQuery = useQuery({
    queryKey: coachWorkoutKeys.clientAssignments(clientId),
    queryFn: () => coachWorkoutsApi.fetchClientAssignments(clientId),
  })

  const historyQuery = useInfiniteQuery({
    queryKey: coachWorkoutKeys.clientHistory(clientId, { pageSize: 20 }),
    queryFn: ({ pageParam }) =>
      coachWorkoutsApi.fetchClientWorkoutHistory(clientId, {
        cursor: pageParam ?? undefined,
        pageSize: 20,
      }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  })

  const cancelMutation = useMutation({
    mutationFn: (assignmentId: string) =>
      coachWorkoutsApi.cancelClientAssignment(clientId, assignmentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.clientAssignments(clientId) })
      showToast('Assignment canceled')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  if (selectedSessionId) {
    return (
      <CoachWorkoutHistory
        clientId={clientId}
        sessionId={selectedSessionId}
        onBack={() => setSelectedSessionId(null)}
      />
    )
  }

  const historyItems = historyQuery.data?.pages.flatMap((page) => page.items) ?? []
  const assignments = assignmentsQuery.data?.items ?? []

  return (
    <div className="space-y-6">
      <WorkoutAssignmentForm clientId={clientId} />

      <section className="space-y-3">
        <h3 className="font-semibold text-text">Assignments</h3>
        {assignmentsQuery.isLoading ? <Spinner label="Loading assignments..." /> : null}
        {!assignmentsQuery.isLoading && assignments.length === 0 ? (
          <p className="text-sm text-textMuted">No assignments yet.</p>
        ) : null}
        {assignments.map((assignment) => (
          <Card key={assignment.id} className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="font-medium text-text">{assignment.title}</p>
              <p className="text-sm text-textMuted">
                {assignment.state} · {assignment.exerciseCount} exercises
                {assignment.scheduledFor ? ` · scheduled ${assignment.scheduledFor}` : ''}
              </p>
            </div>
            {assignment.state === 'available' ? (
              <Button
                size="sm"
                variant="ghost"
                loading={cancelMutation.isPending}
                onClick={() => {
                  if (window.confirm('Cancel this assignment?')) {
                    cancelMutation.mutate(assignment.id)
                  }
                }}
              >
                Cancel
              </Button>
            ) : null}
          </Card>
        ))}
      </section>

      <section className="space-y-3">
        <h3 className="font-semibold text-text">Workout history</h3>
        {historyQuery.isLoading ? <Spinner label="Loading history..." /> : null}
        {!historyQuery.isLoading && historyItems.length === 0 ? (
          <p className="text-sm text-textMuted">No completed workouts yet.</p>
        ) : null}
        {historyItems.map((item) => (
          <button
            key={item.id}
            type="button"
            className="block w-full text-left"
            onClick={() => setSelectedSessionId(item.id)}
          >
            <Card className="transition-colors hover:border-primary/40">
              <p className="font-medium text-text">
                {item.title?.trim() || (item.source === 'assigned' ? 'Assigned workout' : 'Freestyle')}
              </p>
              <p className="text-sm text-textMuted">
                {new Date(item.completedAt).toLocaleString()} ·{' '}
                {formatDurationSeconds(item.durationSeconds)} · {item.completedSetCount} sets
              </p>
            </Card>
          </button>
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
