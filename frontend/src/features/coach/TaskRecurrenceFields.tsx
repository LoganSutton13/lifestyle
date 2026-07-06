import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { cn } from '../../lib/constants'
import {
  DEFAULT_TASK_RECURRENCE,
  WEEKDAY_LABELS,
  type RecurrenceFrequency,
  type TaskRecurrence,
} from './taskRecurrence'

const frequencyOptions = [
  { value: 'daily', label: 'Every day' },
  { value: 'weekly', label: 'On specific days' },
]

export interface TaskRecurrenceFieldsProps {
  value: TaskRecurrence
  onChange: (value: TaskRecurrence) => void
}

export function TaskRecurrenceFields({ value, onChange }: TaskRecurrenceFieldsProps) {
  const intervalUnit = value.recurrenceFrequency === 'daily' ? 'day(s)' : 'week(s)'

  const setFrequency = (recurrenceFrequency: RecurrenceFrequency) => {
    onChange({
      ...value,
      recurrenceFrequency,
      recurrenceDays: recurrenceFrequency === 'daily' ? [] : value.recurrenceDays,
    })
  }

  const toggleDay = (day: number) => {
    const nextDays = value.recurrenceDays.includes(day)
      ? value.recurrenceDays.filter((d) => d !== day)
      : [...value.recurrenceDays, day].sort((a, b) => a - b)
    onChange({ ...value, recurrenceDays: nextDays })
  }

  return (
    <div className="space-y-3">
      <Select
        label="Repeat"
        options={frequencyOptions}
        value={value.recurrenceFrequency}
        onChange={(e) => setFrequency(e.target.value as RecurrenceFrequency)}
      />
      <Input
        label={`Every (${intervalUnit})`}
        type="number"
        min={1}
        value={String(value.recurrenceInterval)}
        onChange={(e) =>
          onChange({
            ...value,
            recurrenceInterval: Math.max(1, Number(e.target.value) || 1),
          })
        }
      />
      {value.recurrenceFrequency === 'weekly' ? (
        <div className="space-y-2">
          <p className="text-sm font-medium text-text">Days</p>
          <div className="flex flex-wrap gap-2">
            {WEEKDAY_LABELS.map((label, day) => {
              const selected = value.recurrenceDays.includes(day)
              return (
                <button
                  key={label}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => toggleDay(day)}
                  className={cn(
                    'min-h-touch rounded-xl border px-3 py-2 text-sm font-medium transition-colors',
                    selected
                      ? 'border-primary bg-primarySoft text-primaryDark'
                      : 'border-border bg-background text-textMuted hover:bg-surface',
                  )}
                >
                  {label}
                </button>
              )
            })}
          </div>
        </div>
      ) : null}
    </div>
  )
}

export { DEFAULT_TASK_RECURRENCE }
