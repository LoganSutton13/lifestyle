import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { Spinner } from '../../components/ui/Spinner'
import { useToast } from '../../components/ui/Toast'
import { getTodayDateString } from '../../lib/date'
import { getErrorMessage } from '../../lib/errors'
import * as coachApi from './api'
import type { CoachTaskItem } from './api'
import { DEFAULT_TASK_RECURRENCE, TaskRecurrenceFields } from './TaskRecurrenceFields'
import { formatRecurrenceSummary, isRecurrenceValid, type TaskRecurrence } from './taskRecurrence'

function taskToRecurrence(task: CoachTaskItem): TaskRecurrence {
  return {
    recurrenceFrequency: task.recurrenceFrequency,
    recurrenceInterval: task.recurrenceInterval,
    recurrenceDays: task.recurrenceDays,
  }
}

export function CoachTasksPanel({ clientId }: { clientId: string }) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [activeFrom, setActiveFrom] = useState(getTodayDateString())
  const [recurrence, setRecurrence] = useState<TaskRecurrence>(DEFAULT_TASK_RECURRENCE)
  const [editingTask, setEditingTask] = useState<CoachTaskItem | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editActiveFrom, setEditActiveFrom] = useState('')
  const [editActiveUntil, setEditActiveUntil] = useState('')
  const [editRecurrence, setEditRecurrence] = useState<TaskRecurrence>(DEFAULT_TASK_RECURRENCE)

  const query = useQuery({
    queryKey: ['coach-client-tasks', clientId],
    queryFn: () => coachApi.fetchClientTasks(clientId),
  })

  useEffect(() => {
    if (editingTask) {
      setEditTitle(editingTask.title)
      setEditDescription(editingTask.description)
      setEditActiveFrom(editingTask.activeFrom)
      setEditActiveUntil(editingTask.activeUntil ?? '')
      setEditRecurrence(taskToRecurrence(editingTask))
    }
  }, [editingTask])

  const createMutation = useMutation({
    mutationFn: () =>
      coachApi.createClientTask(clientId, {
        title,
        description,
        activeFrom,
        ...recurrence,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach-client-tasks', clientId] })
      setTitle('')
      setDescription('')
      setRecurrence(DEFAULT_TASK_RECURRENCE)
      showToast('Activity assigned')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const updateMutation = useMutation({
    mutationFn: () =>
      coachApi.updateClientTask(clientId, editingTask!.id, {
        title: editTitle,
        description: editDescription,
        activeFrom: editActiveFrom,
        activeUntil: editActiveUntil || null,
        ...editRecurrence,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach-client-tasks', clientId] })
      setEditingTask(null)
      showToast('Activity updated')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (taskId: string) => coachApi.deleteClientTask(clientId, taskId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach-client-tasks', clientId] })
      showToast('Activity removed')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const canCreate = title.trim().length > 0 && isRecurrenceValid(recurrence)
  const canSaveEdit = editTitle.trim().length > 0 && isRecurrenceValid(editRecurrence)

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <h3 className="font-semibold text-text">Assign activity</h3>
        <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <label className="flex flex-col gap-1.5 text-sm font-medium text-text">
          Description (optional)
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="rounded-xl border border-border px-3 py-2.5 font-normal"
          />
        </label>
        <Input
          label="Active from"
          type="date"
          value={activeFrom}
          onChange={(e) => setActiveFrom(e.target.value)}
        />
        <TaskRecurrenceFields value={recurrence} onChange={setRecurrence} />
        <Button
          type="button"
          disabled={!canCreate}
          onClick={() => createMutation.mutate()}
          loading={createMutation.isPending}
        >
          Assign activity
        </Button>
      </Card>

      {query.isLoading ? <Spinner label="Loading activities..." /> : null}

      {query.isSuccess ? (
        <div className="space-y-2">
          {query.data.items.map((task) => (
            <Card key={task.id} className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-text">{task.title}</p>
                {task.description ? (
                  <p className="text-sm text-textMuted">{task.description}</p>
                ) : null}
                <p className="mt-1 text-xs text-textMuted">
                  From {task.activeFrom}
                  {task.activeUntil ? ` until ${task.activeUntil}` : null}
                  {' · '}
                  {formatRecurrenceSummary(taskToRecurrence(task))}
                </p>
              </div>
              <div className="flex shrink-0 gap-2">
                <Button type="button" variant="secondary" size="sm" onClick={() => setEditingTask(task)}>
                  Edit
                </Button>
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  onClick={() => deleteMutation.mutate(task.id)}
                >
                  Remove
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : null}

      <Modal
        open={editingTask !== null}
        onClose={() => setEditingTask(null)}
        title="Edit activity"
      >
        <div className="flex flex-col gap-4">
          <Input label="Title" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
          <label className="flex flex-col gap-1.5 text-sm font-medium text-text">
            Description (optional)
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              rows={2}
              className="rounded-xl border border-border px-3 py-2.5 font-normal"
            />
          </label>
          <Input
            label="Active from"
            type="date"
            value={editActiveFrom}
            onChange={(e) => setEditActiveFrom(e.target.value)}
          />
          <Input
            label="Active until (optional)"
            type="date"
            value={editActiveUntil}
            onChange={(e) => setEditActiveUntil(e.target.value)}
          />
          <TaskRecurrenceFields value={editRecurrence} onChange={setEditRecurrence} />
          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="secondary"
              className="flex-1"
              onClick={() => setEditingTask(null)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              className="flex-1"
              disabled={!canSaveEdit}
              loading={updateMutation.isPending}
              onClick={() => updateMutation.mutate()}
            >
              Save
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
