import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import confetti from 'canvas-confetti'
import { ClipboardList } from 'lucide-react'
import { EmptyState } from '../../components/ui/EmptyState'
import { Input } from '../../components/ui/Input'
import { Spinner } from '../../components/ui/Spinner'
import { useToast } from '../../components/ui/Toast'
import { getErrorMessage } from '../../lib/errors'
import { getTodayDateString } from '../../lib/date'
import * as checklistApi from './api'
import { DailyNoteBox } from './DailyNoteBox'
import { TaskItem } from './TaskItem'

export function ChecklistPage() {
  const [date, setDate] = useState(getTodayDateString())
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const previousAllComplete = useRef<boolean | null>(null)

  const query = useQuery({
    queryKey: ['checklist', date],
    queryFn: () => checklistApi.fetchChecklist(date),
  })

  const completionMutation = useMutation({
    mutationFn: ({ taskId, completed }: { taskId: string; completed: boolean }) =>
      checklistApi.updateTaskCompletion(taskId, { date, completed }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['checklist', date] })
    },
    onError: (error) => {
      showToast(getErrorMessage(error), 'error')
    },
  })

  const noteMutation = useMutation({
    mutationFn: (body: string) => checklistApi.saveDailyNote({ date, body }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['checklist', date] })
      showToast('Daily note saved')
    },
    onError: (error) => {
      showToast(getErrorMessage(error), 'error')
    },
  })

  useEffect(() => {
    if (!query.data) {
      return
    }

    const tasks = query.data.tasks
    const allComplete = tasks.length > 0 && tasks.every((task) => task.completed)

    if (previousAllComplete.current === false && allComplete) {
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.7 },
        colors: ['#00B8D9', '#10B981', '#0086A8'],
      })
    }

    previousAllComplete.current = allComplete
  }, [query.data])

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-text">Today&apos;s Checklist</h1>
        <p className="text-sm text-textMuted">Complete your assigned activities</p>
      </div>

      <Input
        label="Date"
        type="date"
        value={date}
        onChange={(event) => setDate(event.target.value)}
      />

      {query.isLoading ? <Spinner label="Loading checklist..." /> : null}

      {query.isError ? (
        <p className="rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          {getErrorMessage(query.error)}
        </p>
      ) : null}

      {query.isSuccess && query.data.tasks.length === 0 ? (
        <EmptyState
          title="No tasks for this day"
          description="Your coach has not assigned activities for the selected date."
          icon={<ClipboardList className="h-8 w-8" />}
        />
      ) : null}

      {query.isSuccess && query.data.tasks.length > 0 ? (
        <div className="space-y-3">
          {query.data.tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              disabled={completionMutation.isPending}
              onToggle={(completed) => completionMutation.mutate({ taskId: task.id, completed })}
            />
          ))}
        </div>
      ) : null}

      {query.isSuccess ? (
        <DailyNoteBox
          value={query.data.note.body}
          updatedAt={query.data.note.updatedAt}
          saving={noteMutation.isPending}
          onSave={(body) => noteMutation.mutate(body)}
        />
      ) : null}
    </div>
  )
}
