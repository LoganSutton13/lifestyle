import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { EmptyState } from '../../../components/ui/EmptyState'
import { Input } from '../../../components/ui/Input'
import { Modal } from '../../../components/ui/Modal'
import { PageTitle } from '../../../components/ui/PageTitle'
import { Spinner } from '../../../components/ui/Spinner'
import { useToast } from '../../../components/ui/Toast'
import { getErrorMessage } from '../../../lib/errors'
import * as coachWorkoutsApi from './api'
import { coachWorkoutKeys } from './queryKeys'

export function WorkoutTemplatesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [createOpen, setCreateOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [notes, setNotes] = useState('')

  const query = useQuery({
    queryKey: coachWorkoutKeys.templates(),
    queryFn: () => coachWorkoutsApi.fetchWorkoutTemplates(),
  })

  const createMutation = useMutation({
    mutationFn: () => coachWorkoutsApi.createWorkoutTemplate({ title: title.trim(), notes }),
    onSuccess: async (template) => {
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.templates() })
      setCreateOpen(false)
      setTitle('')
      setNotes('')
      navigate(`/coach/workouts/templates/${template.id}`)
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const archiveMutation = useMutation({
    mutationFn: coachWorkoutsApi.archiveWorkoutTemplate,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.templates() })
      showToast('Template archived')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <PageTitle>Workout templates</PageTitle>
          <p className="text-sm text-textMuted">Build reusable workouts to assign to clients</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          New template
        </Button>
      </div>

      {query.isLoading ? <Spinner label="Loading templates..." /> : null}

      {!query.isLoading && (query.data?.items.length ?? 0) === 0 ? (
        <EmptyState
          title="No templates yet"
          description="Create a template, add exercises, publish a version, then assign it."
          action={
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              New template
            </Button>
          }
        />
      ) : null}

      <div className="space-y-3">
        {query.data?.items.map((template) => (
          <Card key={template.id} className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <Link
                to={`/coach/workouts/templates/${template.id}`}
                className="text-lg font-semibold text-text hover:text-primary"
              >
                {template.title}
              </Link>
              <p className="text-sm text-textMuted">
                {template.latestPublishedVersionNumber
                  ? `Published v${template.latestPublishedVersionNumber}`
                  : 'No published version'}
                {template.hasDraft ? ' · Draft in progress' : ''}
              </p>
            </div>
            <div className="flex gap-2">
              <Link to={`/coach/workouts/templates/${template.id}`}>
                <Button size="sm" variant="secondary">
                  Edit
                </Button>
              </Link>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  if (window.confirm(`Archive ${template.title}?`)) {
                    archiveMutation.mutate(template.id)
                  }
                }}
              >
                Archive
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="New template">
        <div className="space-y-4">
          <Input
            label="Title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Upper body day"
          />
          <label className="flex flex-col gap-1.5 text-sm font-medium text-text">
            Notes
            <textarea
              rows={3}
              className="rounded-xl border border-border px-3 py-2.5 font-normal"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
            />
          </label>
          <Button
            className="w-full"
            disabled={!title.trim()}
            loading={createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            Create template
          </Button>
        </div>
      </Modal>
    </div>
  )
}
