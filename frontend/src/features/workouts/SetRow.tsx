import { useEffect, useRef, useState } from 'react'
import { Check, Trash2, Undo2 } from 'lucide-react'
import { cn } from '../../lib/cn'
import { WEIGHT_UNITS } from '../../lib/units'
import type { TrackingType } from '../exercises/types'
import type { SetType, UpdateSetPayload, WorkoutSet } from './types'

const SET_TYPE_OPTIONS: { value: SetType; label: string }[] = [
  { value: 'normal', label: 'Normal' },
  { value: 'warmup', label: 'Warmup' },
  { value: 'drop', label: 'Drop' },
  { value: 'failure', label: 'Failure' },
]

const AUTOSAVE_DEBOUNCE_MS = 500

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

export interface SetRowProps {
  set: WorkoutSet
  index: number
  trackingType: TrackingType
  isUnilateral: boolean
  isFinal: boolean
  readOnly?: boolean
  onSave: (payload: UpdateSetPayload) => Promise<WorkoutSet>
  onDelete?: () => void
}

function toNumericString(value: number | string | null): string {
  if (value === null || value === undefined) return ''
  return String(value)
}

export function SetRow({
  set,
  index,
  trackingType,
  isUnilateral,
  isFinal,
  readOnly,
  onSave,
  onDelete,
}: SetRowProps) {
  const [setType, setSetType] = useState<SetType>(set.setType)
  const [reps, setReps] = useState(toNumericString(set.reps))
  const [loadValue, setLoadValue] = useState(toNumericString(set.loadValue))
  const [loadUnitKey, setLoadUnitKey] = useState(set.loadUnitKey ?? 'lb')
  const [durationSeconds, setDurationSeconds] = useState(toNumericString(set.durationSeconds))
  const [status, setStatus] = useState<SaveStatus>('idle')
  const [fieldError, setFieldError] = useState<string | null>(null)
  const debounceRef = useRef<number | null>(null)
  const lastPayloadRef = useRef<UpdateSetPayload | null>(null)
  const isComplete = set.completedAt !== null

  useEffect(() => {
    setSetType(set.setType)
    setReps(toNumericString(set.reps))
    setLoadValue(toNumericString(set.loadValue))
    setLoadUnitKey(set.loadUnitKey ?? 'lb')
    setDurationSeconds(toNumericString(set.durationSeconds))
    setStatus('idle')
    setFieldError(null)
    // Only resync when a different row instance loads, not on every parent re-render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [set.id])

  useEffect(() => {
    return () => {
      if (debounceRef.current !== null) {
        window.clearTimeout(debounceRef.current)
      }
    }
  }, [])

  function validate(): boolean {
    if (reps !== '' && Number(reps) < 0) {
      setFieldError('Reps must not be negative')
      return false
    }
    if (loadValue !== '' && Number(loadValue) < 0) {
      setFieldError('Load must not be negative')
      return false
    }
    if (durationSeconds !== '' && Number(durationSeconds) < 0) {
      setFieldError('Duration must not be negative')
      return false
    }
    setFieldError(null)
    return true
  }

  function buildPayload(overrides: Partial<UpdateSetPayload> = {}): UpdateSetPayload {
    const effectiveLoadValue = overrides.loadValue !== undefined ? overrides.loadValue : loadValue === '' ? null : loadValue
    const payload: UpdateSetPayload = {
      setType,
      reps: reps === '' ? null : Number(reps),
      loadValue: loadValue === '' ? null : loadValue,
      loadUnitKey: effectiveLoadValue === null ? null : loadUnitKey,
      durationSeconds: durationSeconds === '' ? null : Number(durationSeconds),
      ...overrides,
    }
    return payload
  }

  async function persist(payload: UpdateSetPayload) {
    if (!validate()) {
      return
    }
    lastPayloadRef.current = payload
    setStatus('saving')
    try {
      await onSave(payload)
      setStatus('saved')
    } catch {
      setStatus('error')
    }
  }

  function scheduleSave(overrides: Partial<UpdateSetPayload> = {}) {
    if (debounceRef.current !== null) {
      window.clearTimeout(debounceRef.current)
    }
    debounceRef.current = window.setTimeout(() => {
      void persist(buildPayload(overrides))
    }, AUTOSAVE_DEBOUNCE_MS)
  }

  function saveNow(overrides: Partial<UpdateSetPayload> = {}) {
    if (debounceRef.current !== null) {
      window.clearTimeout(debounceRef.current)
      debounceRef.current = null
    }
    void persist(buildPayload(overrides))
  }

  function handleRetry() {
    if (lastPayloadRef.current) {
      void persist(lastPayloadRef.current)
    }
  }

  function handleToggleComplete() {
    if (!isComplete) {
      if (trackingType === 'reps_load') {
        if (reps === '' || loadValue === '') {
          setFieldError(
            reps === '' ? 'Reps are required' : 'Load is required',
          )
          return
        }
      } else if (trackingType === 'reps_only' && reps === '') {
        setFieldError('Reps are required')
        return
      } else if (trackingType === 'duration' && durationSeconds === '') {
        setFieldError('Duration is required')
        return
      }
    }
    saveNow({ completed: !isComplete })
  }

  const rowId = `set-row-${set.id}`
  const errorId = `${rowId}-error`

  if (readOnly) {
    return (
      <div className={cn('flex items-center gap-3 rounded-xl border border-border px-3 py-2.5', isComplete && 'bg-primarySoft/30')}>
        <span className="w-5 shrink-0 text-sm font-semibold text-textMuted">{index}</span>
        <span className="w-16 shrink-0 text-xs uppercase text-textMuted">{setType}</span>
        <span className="flex-1 text-sm text-text">
          {trackingType === 'duration'
            ? `${set.durationSeconds ?? '-'} sec`
            : trackingType === 'reps_only'
              ? `${set.reps ?? '-'} reps${isUnilateral ? ' / side' : ''}`
              : `${set.loadValue ?? '-'} ${set.loadUnitKey ?? ''} x ${set.reps ?? '-'}${isUnilateral ? ' / side' : ''}`}
        </span>
        <span className="text-xs font-medium text-textMuted">{isComplete ? 'Completed' : 'Not completed'}</span>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'flex flex-col gap-2 rounded-xl border border-border p-3',
        isComplete && 'border-success bg-success/5',
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="w-5 shrink-0 text-sm font-semibold text-textMuted" aria-hidden="true">
          {index}
        </span>

        <select
          aria-label={`Set ${index} type`}
          value={setType}
          onChange={(event) => {
            setSetType(event.target.value as SetType)
            scheduleSave({ setType: event.target.value as SetType })
          }}
          className="min-h-touch rounded-lg border border-border bg-background px-2 text-sm text-text"
        >
          {SET_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {trackingType !== 'duration' ? (
          <label className="sr-only" htmlFor={`${rowId}-load`}>
            Load
          </label>
        ) : null}

        {trackingType === 'reps_load' ? (
          <div className="flex items-center gap-1">
            <input
              id={`${rowId}-load`}
              type="text"
              inputMode="decimal"
              placeholder="0"
              value={loadValue}
              onChange={(event) => {
                setLoadValue(event.target.value)
                scheduleSave({ loadValue: event.target.value === '' ? null : event.target.value })
              }}
              onBlur={() => saveNow()}
              aria-describedby={fieldError ? errorId : undefined}
              className="min-h-touch w-16 rounded-lg border border-border bg-background px-2 text-base text-text"
            />
            <select
              aria-label={`Set ${index} load unit`}
              value={loadUnitKey}
              onChange={(event) => {
                setLoadUnitKey(event.target.value)
                scheduleSave({ loadUnitKey: event.target.value })
              }}
              className="min-h-touch rounded-lg border border-border bg-background px-1 text-sm text-text"
            >
              {WEIGHT_UNITS.map((unit) => (
                <option key={unit.key} value={unit.key}>
                  {unit.symbol}
                </option>
              ))}
            </select>
            <span className="text-textMuted" aria-hidden="true">
              &times;
            </span>
          </div>
        ) : null}

        {trackingType !== 'duration' ? (
          <div className="flex items-center gap-1">
            <input
              aria-label={`Set ${index} reps`}
              type="text"
              inputMode="numeric"
              placeholder="0"
              value={reps}
              onChange={(event) => {
                setReps(event.target.value)
                scheduleSave({ reps: event.target.value === '' ? null : Number(event.target.value) })
              }}
              onBlur={() => saveNow()}
              className="min-h-touch w-14 rounded-lg border border-border bg-background px-2 text-base text-text"
            />
            <span className="text-xs text-textMuted">reps{isUnilateral ? '/side' : ''}</span>
          </div>
        ) : (
          <div className="flex items-center gap-1">
            <input
              aria-label={`Set ${index} duration in seconds`}
              type="text"
              inputMode="numeric"
              placeholder="0"
              value={durationSeconds}
              onChange={(event) => {
                setDurationSeconds(event.target.value)
                scheduleSave({
                  durationSeconds: event.target.value === '' ? null : Number(event.target.value),
                })
              }}
              onBlur={() => saveNow()}
              className="min-h-touch w-16 rounded-lg border border-border bg-background px-2 text-base text-text"
            />
            <span className="text-xs text-textMuted">sec</span>
          </div>
        )}

        <button
          type="button"
          onClick={handleToggleComplete}
          aria-pressed={isComplete}
          className={cn(
            'ml-auto flex min-h-touch items-center gap-1 rounded-lg px-3 text-sm font-medium transition-colors',
            isComplete ? 'bg-success text-white' : 'bg-primarySoft text-primaryDark hover:bg-primary/20',
          )}
        >
          {isComplete ? <Undo2 className="h-4 w-4" aria-hidden="true" /> : <Check className="h-4 w-4" aria-hidden="true" />}
          {isComplete ? 'Completed' : 'Complete'}
        </button>

        {!isFinal && onDelete ? (
          <button
            type="button"
            aria-label={`Delete set ${index}`}
            onClick={onDelete}
            className="flex min-h-touch min-w-touch items-center justify-center rounded-lg text-textMuted hover:bg-danger/10 hover:text-danger"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {fieldError ? (
        <p id={errorId} className="text-sm text-danger">
          {fieldError}
        </p>
      ) : null}

      <div className="flex items-center gap-2 text-xs">
        {status === 'saving' ? <span className="text-textMuted">Saving...</span> : null}
        {status === 'saved' ? <span className="text-success">Saved</span> : null}
        {status === 'error' ? (
          <span className="flex items-center gap-2 text-danger">
            Not saved
            <button type="button" onClick={handleRetry} className="font-semibold underline">
              Retry
            </button>
          </span>
        ) : null}
      </div>
    </div>
  )
}
