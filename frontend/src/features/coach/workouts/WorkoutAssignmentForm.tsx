import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { Input } from '../../../components/ui/Input'
import { Select } from '../../../components/ui/Select'
import { Spinner } from '../../../components/ui/Spinner'
import { useToast } from '../../../components/ui/Toast'
import { getErrorMessage } from '../../../lib/errors'
import * as coachWorkoutsApi from './api'
import { coachWorkoutKeys } from './queryKeys'

export function WorkoutAssignmentForm({ clientId }: { clientId: string }) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [templateId, setTemplateId] = useState('')
  const [versionId, setVersionId] = useState('')
  const [scheduledFor, setScheduledFor] = useState('')
  const [dueAt, setDueAt] = useState('')
  const [notes, setNotes] = useState('')

  const templatesQuery = useQuery({
    queryKey: coachWorkoutKeys.templates(),
    queryFn: () => coachWorkoutsApi.fetchWorkoutTemplates(),
  })

  const detailQuery = useQuery({
    queryKey: coachWorkoutKeys.template(templateId),
    queryFn: () => coachWorkoutsApi.fetchWorkoutTemplate(templateId),
    enabled: Boolean(templateId),
  })

  const publishedVersions = useMemo(
    () => (detailQuery.data?.versions ?? []).filter((version) => version.status === 'published'),
    [detailQuery.data],
  )

  const assignMutation = useMutation({
    mutationFn: () =>
      coachWorkoutsApi.createClientAssignment(clientId, {
        templateVersionId: versionId,
        scheduledFor: scheduledFor || null,
        dueAt: dueAt ? new Date(dueAt).toISOString() : null,
        notes,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.clientAssignments(clientId) })
      setNotes('')
      setScheduledFor('')
      setDueAt('')
      showToast('Workout assigned')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const templateOptions = [
    { value: '', label: 'Select template' },
    ...(templatesQuery.data?.items
      .filter((item) => item.latestPublishedVersionNumber != null)
      .map((item) => ({ value: item.id, label: item.title })) ?? []),
  ]

  const versionOptions = [
    { value: '', label: 'Select published version' },
    ...publishedVersions.map((version) => ({
      value: version.id,
      label: `v${version.versionNumber} — ${version.title}`,
    })),
  ]

  return (
    <Card className="space-y-3">
      <h3 className="font-semibold text-text">Assign workout</h3>
      {templatesQuery.isLoading ? <Spinner label="Loading templates..." /> : null}
      <Select
        label="Template"
        options={templateOptions}
        value={templateId}
        onChange={(event) => {
          setTemplateId(event.target.value)
          setVersionId('')
        }}
      />
      <Select
        label="Published version"
        options={versionOptions}
        value={versionId}
        disabled={!templateId}
        onChange={(event) => setVersionId(event.target.value)}
      />
      <Input
        label="Scheduled for (optional)"
        type="date"
        value={scheduledFor}
        onChange={(event) => setScheduledFor(event.target.value)}
      />
      <Input
        label="Due at (optional)"
        type="datetime-local"
        value={dueAt}
        onChange={(event) => setDueAt(event.target.value)}
      />
      <label className="flex flex-col gap-1.5 text-sm font-medium text-text">
        Notes
        <textarea
          rows={2}
          className="rounded-xl border border-border px-3 py-2.5 font-normal"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
        />
      </label>
      <Button
        disabled={!versionId}
        loading={assignMutation.isPending}
        onClick={() => assignMutation.mutate()}
      >
        Assign workout
      </Button>
    </Card>
  )
}
