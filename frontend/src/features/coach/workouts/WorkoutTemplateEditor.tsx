import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Plus, Trash2 } from 'lucide-react'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { Input } from '../../../components/ui/Input'
import { PageTitle } from '../../../components/ui/PageTitle'
import { Spinner } from '../../../components/ui/Spinner'
import { useToast } from '../../../components/ui/Toast'
import { getErrorMessage } from '../../../lib/errors'
import { ExercisePickerSheet } from '../../exercises/ExercisePickerSheet'
import type { Exercise } from '../../exercises/types'
import * as coachWorkoutsApi from './api'
import { coachWorkoutKeys } from './queryKeys'
import type { TemplateExerciseInput, TemplateSetInput, TemplateVersion } from './types'

interface DraftSetLocal extends TemplateSetInput {
  key: string
}

interface DraftExerciseLocal extends Omit<TemplateExerciseInput, 'sets'> {
  key: string
  exerciseName: string
  sets: DraftSetLocal[]
}

function versionToDraft(version: TemplateVersion): {
  title: string
  notes: string
  exercises: DraftExerciseLocal[]
} {
  return {
    title: version.title,
    notes: version.notes,
    exercises: [...version.exercises]
      .sort((a, b) => a.position - b.position)
      .map((exercise, index) => ({
        key: exercise.id,
        position: index,
        exerciseId: exercise.exerciseId,
        exerciseName: exercise.exerciseName,
        isUnilateral: exercise.isUnilateral,
        restSeconds: exercise.restSeconds,
        notes: exercise.notes,
        sets: [...exercise.sets]
          .sort((a, b) => a.position - b.position)
          .map((set, setIndex) => ({
            key: set.id,
            position: setIndex,
            setType: set.setType,
            targetRepsMin: set.targetRepsMin,
            targetRepsMax: set.targetRepsMax,
            targetLoadValue: set.targetLoadValue,
            targetLoadUnitKey: set.targetLoadUnitKey,
            targetDurationSeconds: set.targetDurationSeconds,
            targetRpe: set.targetRpe,
            notes: set.notes,
          })),
      })),
  }
}

function toPayload(draft: {
  title: string
  notes: string
  exercises: DraftExerciseLocal[]
}) {
  return {
    title: draft.title.trim(),
    notes: draft.notes,
    exercises: draft.exercises.map((exercise, index) => ({
      position: index,
      exerciseId: exercise.exerciseId,
      isUnilateral: exercise.isUnilateral,
      restSeconds: exercise.restSeconds,
      notes: exercise.notes,
      sets: exercise.sets.map((set, setIndex) => ({
        position: setIndex,
        setType: set.setType ?? 'normal',
        targetRepsMin: set.targetRepsMin ?? null,
        targetRepsMax: set.targetRepsMax ?? null,
        targetLoadValue: set.targetLoadValue ?? null,
        targetLoadUnitKey: set.targetLoadUnitKey ?? null,
        targetDurationSeconds: set.targetDurationSeconds ?? null,
        targetRpe: set.targetRpe ?? null,
        notes: set.notes ?? '',
      })),
    })),
  }
}

export function WorkoutTemplateEditor() {
  const { templateId = '' } = useParams()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [pickerOpen, setPickerOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [notes, setNotes] = useState('')
  const [exercises, setExercises] = useState<DraftExerciseLocal[]>([])
  const [hydratedVersionId, setHydratedVersionId] = useState<string | null>(null)

  const query = useQuery({
    queryKey: coachWorkoutKeys.template(templateId),
    queryFn: () => coachWorkoutsApi.fetchWorkoutTemplate(templateId),
    enabled: Boolean(templateId),
  })

  const draftVersion = useMemo(() => {
    const versions = query.data?.versions ?? []
    return (
      versions.find((version) => version.status === 'draft') ??
      [...versions].sort((a, b) => b.versionNumber - a.versionNumber)[0] ??
      null
    )
  }, [query.data])

  const publishedVersions = useMemo(
    () => (query.data?.versions ?? []).filter((version) => version.status === 'published'),
    [query.data],
  )

  useEffect(() => {
    if (!draftVersion || draftVersion.id === hydratedVersionId) return
    const next = versionToDraft(draftVersion)
    setTitle(next.title)
    setNotes(next.notes)
    setExercises(next.exercises)
    setHydratedVersionId(draftVersion.id)
  }, [draftVersion, hydratedVersionId])

  const ensureDraftMutation = useMutation({
    mutationFn: () => coachWorkoutsApi.createTemplateDraft(templateId),
    onSuccess: async (version) => {
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.template(templateId) })
      const next = versionToDraft(version)
      setTitle(next.title)
      setNotes(next.notes)
      setExercises(next.exercises)
      setHydratedVersionId(version.id)
      showToast('Draft ready to edit')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      let versionId = draftVersion?.status === 'draft' ? draftVersion.id : null
      if (!versionId) {
        const created = await coachWorkoutsApi.createTemplateDraft(templateId)
        versionId = created.id
      }
      return coachWorkoutsApi.updateTemplateDraft(
        versionId,
        toPayload({ title, notes, exercises }),
      )
    },
    onSuccess: async (version) => {
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.template(templateId) })
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.templates() })
      setHydratedVersionId(version.id)
      showToast('Draft saved')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const publishMutation = useMutation({
    mutationFn: async () => {
      const saved = await saveMutation.mutateAsync()
      return coachWorkoutsApi.publishTemplateVersion(saved.id)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.template(templateId) })
      await queryClient.invalidateQueries({ queryKey: coachWorkoutKeys.templates() })
      showToast('Template published')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const addExercise = (exercise: Exercise) => {
    setExercises((current) => [
      ...current,
      {
        key: `local-${exercise.id}-${Date.now()}`,
        position: current.length,
        exerciseId: exercise.id,
        exerciseName: exercise.name,
        isUnilateral: exercise.defaultUnilateral,
        restSeconds: exercise.defaultRestSeconds,
        notes: '',
        sets: [
          {
            key: `set-${Date.now()}`,
            position: 0,
            setType: 'normal',
            targetRepsMin: 8,
            targetRepsMax: 12,
            targetLoadValue: null,
            targetLoadUnitKey: 'lb',
            targetDurationSeconds: null,
            targetRpe: null,
            notes: '',
          },
        ],
      },
    ])
    setPickerOpen(false)
  }

  if (query.isLoading) {
    return <Spinner label="Loading template..." />
  }

  if (!query.data || !draftVersion) {
    return (
      <div className="space-y-4">
        <Link to="/coach/workouts/templates" className="text-sm font-medium text-primary">
          Back to templates
        </Link>
        <p className="text-sm text-danger">Template not found.</p>
      </div>
    )
  }

  const isDraft = draftVersion.status === 'draft'
  const existingExerciseIds = exercises.map((item) => item.exerciseId)

  return (
    <div className="space-y-5">
      <Link
        to="/coach/workouts/templates"
        className="inline-flex min-h-touch items-center gap-2 text-sm font-medium text-primary hover:text-primaryDark"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to templates
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <PageTitle>{title || 'Template'}</PageTitle>
          <p className="text-sm text-textMuted">
            {isDraft
              ? `Editing draft (based on v${draftVersion.versionNumber})`
              : `Viewing published v${draftVersion.versionNumber} — create a draft to edit`}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {!isDraft ? (
            <Button
              variant="secondary"
              loading={ensureDraftMutation.isPending}
              onClick={() => ensureDraftMutation.mutate()}
            >
              Edit as new draft
            </Button>
          ) : (
            <>
              <Button
                variant="secondary"
                loading={saveMutation.isPending}
                onClick={() => saveMutation.mutate()}
              >
                Save draft
              </Button>
              <Button loading={publishMutation.isPending} onClick={() => publishMutation.mutate()}>
                Publish
              </Button>
            </>
          )}
        </div>
      </div>

      <Card className="space-y-3">
        <Input
          label="Title"
          value={title}
          disabled={!isDraft}
          onChange={(event) => setTitle(event.target.value)}
        />
        <label className="flex flex-col gap-1.5 text-sm font-medium text-text">
          Notes
          <textarea
            rows={3}
            disabled={!isDraft}
            className="rounded-xl border border-border px-3 py-2.5 font-normal disabled:opacity-60"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </label>
      </Card>

      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-text">Exercises</h2>
        {isDraft ? (
          <Button size="sm" variant="secondary" onClick={() => setPickerOpen(true)}>
            <Plus className="h-4 w-4" />
            Add exercise
          </Button>
        ) : null}
      </div>

      {exercises.length === 0 ? (
        <p className="text-sm text-textMuted">No exercises yet.</p>
      ) : null}

      {exercises.map((exercise, exerciseIndex) => (
        <Card key={exercise.key} className="space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold text-text">{exercise.exerciseName}</h3>
              <label className="mt-2 flex items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  disabled={!isDraft}
                  checked={Boolean(exercise.isUnilateral)}
                  onChange={(event) =>
                    setExercises((current) =>
                      current.map((item, index) =>
                        index === exerciseIndex
                          ? { ...item, isUnilateral: event.target.checked }
                          : item,
                      ),
                    )
                  }
                />
                Unilateral
              </label>
            </div>
            {isDraft ? (
              <Button
                size="sm"
                variant="ghost"
                aria-label="Remove exercise"
                onClick={() =>
                  setExercises((current) => current.filter((_, index) => index !== exerciseIndex))
                }
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            ) : null}
          </div>

          <div className="space-y-2">
            {exercise.sets.map((set, setIndex) => (
              <div key={set.key} className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <Input
                  label="Reps min"
                  type="number"
                  disabled={!isDraft}
                  value={set.targetRepsMin ?? ''}
                  onChange={(event) => {
                    const value = event.target.value === '' ? null : Number(event.target.value)
                    setExercises((current) =>
                      current.map((item, index) =>
                        index === exerciseIndex
                          ? {
                              ...item,
                              sets: item.sets.map((row, rowIndex) =>
                                rowIndex === setIndex ? { ...row, targetRepsMin: value } : row,
                              ),
                            }
                          : item,
                      ),
                    )
                  }}
                />
                <Input
                  label="Reps max"
                  type="number"
                  disabled={!isDraft}
                  value={set.targetRepsMax ?? ''}
                  onChange={(event) => {
                    const value = event.target.value === '' ? null : Number(event.target.value)
                    setExercises((current) =>
                      current.map((item, index) =>
                        index === exerciseIndex
                          ? {
                              ...item,
                              sets: item.sets.map((row, rowIndex) =>
                                rowIndex === setIndex ? { ...row, targetRepsMax: value } : row,
                              ),
                            }
                          : item,
                      ),
                    )
                  }}
                />
                <Input
                  label="Load"
                  disabled={!isDraft}
                  value={set.targetLoadValue ?? ''}
                  onChange={(event) => {
                    const value = event.target.value === '' ? null : event.target.value
                    setExercises((current) =>
                      current.map((item, index) =>
                        index === exerciseIndex
                          ? {
                              ...item,
                              sets: item.sets.map((row, rowIndex) =>
                                rowIndex === setIndex
                                  ? {
                                      ...row,
                                      targetLoadValue: value,
                                      targetLoadUnitKey: value ? row.targetLoadUnitKey ?? 'lb' : null,
                                    }
                                  : row,
                              ),
                            }
                          : item,
                      ),
                    )
                  }}
                />
                <Input
                  label="Rest (s)"
                  type="number"
                  disabled={!isDraft}
                  value={exercise.restSeconds}
                  onChange={(event) => {
                    const value = Number(event.target.value)
                    setExercises((current) =>
                      current.map((item, index) =>
                        index === exerciseIndex
                          ? { ...item, restSeconds: Number.isFinite(value) ? value : 0 }
                          : item,
                      ),
                    )
                  }}
                />
              </div>
            ))}
          </div>

          {isDraft ? (
            <Button
              size="sm"
              variant="secondary"
              onClick={() =>
                setExercises((current) =>
                  current.map((item, index) =>
                    index === exerciseIndex
                      ? {
                          ...item,
                          sets: [
                            ...item.sets,
                            {
                              key: `set-${Date.now()}-${item.sets.length}`,
                              position: item.sets.length,
                              setType: 'normal',
                              targetRepsMin: 8,
                              targetRepsMax: 12,
                              targetLoadValue: null,
                              targetLoadUnitKey: 'lb',
                              targetDurationSeconds: null,
                              targetRpe: null,
                              notes: '',
                            },
                          ],
                        }
                      : item,
                  ),
                )
              }
            >
              Add prescribed set
            </Button>
          ) : null}
        </Card>
      ))}

      {publishedVersions.length > 0 ? (
        <section className="space-y-2">
          <h2 className="text-lg font-semibold text-text">Published versions</h2>
          <ul className="space-y-1 text-sm text-textMuted">
            {publishedVersions.map((version) => (
              <li key={version.id}>
                v{version.versionNumber} · {version.title} ·{' '}
                {version.publishedAt ? new Date(version.publishedAt).toLocaleString() : '—'}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <ExercisePickerSheet
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        existingExerciseIds={existingExerciseIds}
        onSelect={addExercise}
      />
    </div>
  )
}
