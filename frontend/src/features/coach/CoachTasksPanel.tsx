import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Spinner } from '../../components/ui/Spinner'
import { useToast } from '../../components/ui/Toast'
import { getTodayDateString } from '../../lib/date'
import { getErrorMessage } from '../../lib/errors'
import * as coachApi from './api'

export function CoachTasksPanel({ clientId }: { clientId: string }) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [activeFrom, setActiveFrom] = useState(getTodayDateString())

  const query = useQuery({
    queryKey: ['coach-client-tasks', clientId],
    queryFn: () => coachApi.fetchClientTasks(clientId),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      coachApi.createClientTask(clientId, {
        title,
        description,
        activeFrom,
        repeatsDaily: true,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach-client-tasks', clientId] })
      setTitle('')
      setDescription('')
      showToast('Activity assigned')
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

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <h3 className="font-semibold text-text">Assign daily activity</h3>
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
        <Button type="button" onClick={() => createMutation.mutate()} loading={createMutation.isPending}>
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
                <p className="mt-1 text-xs text-textMuted">From {task.activeFrom}</p>
              </div>
              <Button
                type="button"
                variant="danger"
                size="sm"
                onClick={() => deleteMutation.mutate(task.id)}
              >
                Remove
              </Button>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  )
}
