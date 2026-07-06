export type RecurrenceFrequency = 'daily' | 'weekly'

export interface TaskRecurrence {
  recurrenceFrequency: RecurrenceFrequency
  recurrenceInterval: number
  recurrenceDays: number[]
}

export const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const

export const DEFAULT_TASK_RECURRENCE: TaskRecurrence = {
  recurrenceFrequency: 'daily',
  recurrenceInterval: 1,
  recurrenceDays: [],
}

export function isRecurrenceValid(recurrence: TaskRecurrence): boolean {
  if (recurrence.recurrenceInterval < 1) {
    return false
  }
  if (recurrence.recurrenceFrequency === 'weekly') {
    return recurrence.recurrenceDays.length > 0
  }
  return true
}

export function formatRecurrenceSummary(recurrence: TaskRecurrence): string {
  const { recurrenceFrequency, recurrenceInterval, recurrenceDays } = recurrence

  if (recurrenceFrequency === 'daily') {
    if (recurrenceInterval === 1) {
      return 'Every day'
    }
    return `Every ${recurrenceInterval} days`
  }

  const dayLabels = recurrenceDays.map((day) => WEEKDAY_LABELS[day]).join(', ')
  const weekLabel = recurrenceInterval === 1 ? 'every week' : `every ${recurrenceInterval} weeks`
  return `${dayLabels} · ${weekLabel}`
}
