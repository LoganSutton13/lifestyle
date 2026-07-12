import { useEffect } from 'react'
import { useForm, type Resolver } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { EQUIPMENT_OPTIONS, MUSCLE_GROUP_OPTIONS, type Exercise, type TrackingType } from './types'

const schema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(160),
  equipmentKey: z.string().min(1, 'Equipment is required'),
  trackingType: z.enum(['reps_load', 'reps_only', 'duration']),
  defaultUnilateral: z.boolean(),
  defaultRestSeconds: z.coerce.number().int().min(0).max(3600),
  primaryMuscleKey: z.string().min(1, 'Primary muscle is required'),
  secondaryMuscleKeys: z.array(z.string()),
  instructions: z.string().max(5000),
})

export type CreateExerciseFormValues = z.infer<typeof schema>

export interface CreateExerciseFormProps {
  initial?: Exercise | null
  saving?: boolean
  submitLabel?: string
  onSubmit: (values: {
    name: string
    equipmentKey: string
    trackingType: TrackingType
    defaultUnilateral: boolean
    defaultRestSeconds: number
    primaryMuscleKeys: string[]
    secondaryMuscleKeys: string[]
    instructions: string
  }) => void
  onCancel?: () => void
  lockIdentityFields?: boolean
}

function toDefaults(initial?: Exercise | null): CreateExerciseFormValues {
  return {
    name: initial?.name ?? '',
    equipmentKey: initial?.equipment.key ?? 'barbell',
    trackingType: initial?.trackingType ?? 'reps_load',
    defaultUnilateral: initial?.defaultUnilateral ?? false,
    defaultRestSeconds: initial?.defaultRestSeconds ?? 120,
    primaryMuscleKey: initial?.primaryMuscles[0]?.key ?? 'chest',
    secondaryMuscleKeys: initial?.secondaryMuscles.map((m) => m.key) ?? [],
    instructions: initial?.instructions ?? '',
  }
}

export function CreateExerciseForm({
  initial,
  saving,
  submitLabel = 'Save exercise',
  onSubmit,
  onCancel,
  lockIdentityFields = false,
}: CreateExerciseFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<CreateExerciseFormValues>({
    resolver: zodResolver(schema) as Resolver<CreateExerciseFormValues>,
    defaultValues: toDefaults(initial),
  })

  const secondaryMuscleKeys = watch('secondaryMuscleKeys')

  useEffect(() => {
    reset(toDefaults(initial))
  }, [initial, reset])

  return (
    <form
      className="space-y-4"
      onSubmit={handleSubmit((values) => {
        onSubmit({
          name: values.name.trim(),
          equipmentKey: values.equipmentKey,
          trackingType: values.trackingType,
          defaultUnilateral: values.defaultUnilateral,
          defaultRestSeconds: values.defaultRestSeconds,
          primaryMuscleKeys: [values.primaryMuscleKey],
          secondaryMuscleKeys: values.secondaryMuscleKeys.filter((key) => key !== values.primaryMuscleKey),
          instructions: values.instructions.trim(),
        })
      })}
    >
      <p className="rounded-xl bg-primarySoft px-3 py-2 text-sm text-primaryDark">
        Exercises added here are available to every client and coach.
      </p>

      <Input label="Name" error={errors.name?.message} {...register('name')} />

      <Select
        label="Equipment"
        error={errors.equipmentKey?.message}
        disabled={lockIdentityFields}
        options={EQUIPMENT_OPTIONS.map((option) => ({
          value: option.key,
          label: option.displayName,
        }))}
        {...register('equipmentKey')}
      />

      <Select
        label="Tracking type"
        error={errors.trackingType?.message}
        disabled={lockIdentityFields}
        options={[
          { value: 'reps_load', label: 'Reps & Load' },
          { value: 'reps_only', label: 'Reps only' },
          { value: 'duration', label: 'Duration' },
        ]}
        {...register('trackingType')}
      />

      <Select
        label="Primary muscle"
        error={errors.primaryMuscleKey?.message}
        options={MUSCLE_GROUP_OPTIONS.map((option) => ({
          value: option.key,
          label: option.displayName,
        }))}
        {...register('primaryMuscleKey')}
      />

      <fieldset className="space-y-2">
        <legend className="text-sm font-medium text-text">Secondary muscles</legend>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {MUSCLE_GROUP_OPTIONS.map((option) => {
            const checked = secondaryMuscleKeys.includes(option.key)
            return (
              <label key={option.key} className="flex min-h-touch items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(event) => {
                    const next = event.target.checked
                      ? [...secondaryMuscleKeys, option.key]
                      : secondaryMuscleKeys.filter((key) => key !== option.key)
                    setValue('secondaryMuscleKeys', next, { shouldDirty: true })
                  }}
                />
                {option.displayName}
              </label>
            )
          })}
        </div>
      </fieldset>

      <label className="flex min-h-touch items-center gap-2 text-sm text-text">
        <input type="checkbox" {...register('defaultUnilateral')} />
        Default unilateral (per side)
      </label>

      <Input
        label="Default rest (seconds)"
        type="number"
        min={0}
        max={3600}
        error={errors.defaultRestSeconds?.message}
        {...register('defaultRestSeconds')}
      />

      <div className="flex w-full flex-col gap-1.5">
        <label htmlFor="exercise-instructions" className="text-sm font-medium text-text">
          Instructions
        </label>
        <textarea
          id="exercise-instructions"
          rows={4}
          className="min-h-touch w-full rounded-xl border border-border bg-background px-3 py-2.5 text-base text-text outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
          {...register('instructions')}
        />
        {errors.instructions?.message ? (
          <p className="text-sm text-danger">{errors.instructions.message}</p>
        ) : null}
      </div>

      <div className="flex gap-3">
        {onCancel ? (
          <Button type="button" variant="secondary" className="flex-1" onClick={onCancel}>
            Cancel
          </Button>
        ) : null}
        <Button type="submit" className="flex-1" loading={saving}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
