import { format, parseISO, subMonths } from 'date-fns'

export function formatDateForApi(date: Date): string {
  return format(date, 'yyyy-MM-dd')
}

export function formatDateTimeForApi(date: Date): string {
  return date.toISOString()
}

export function formatDisplayDate(dateStr: string): string {
  return format(parseISO(dateStr), 'MMM d, yyyy')
}

export function formatDisplayDateTime(dateStr: string): string {
  return format(parseISO(dateStr), 'MMM d, yyyy h:mm a')
}

export function getTodayDateString(): string {
  return format(new Date(), 'yyyy-MM-dd')
}

export function getDefaultMeasurementRange(): { startDate: string; endDate: string } {
  const end = new Date()
  const start = subMonths(end, 1)
  return {
    startDate: formatDateForApi(start),
    endDate: formatDateForApi(end),
  }
}

export function getRangeFromPreset(months: number): { startDate: string; endDate: string } {
  const end = new Date()
  const start = subMonths(end, months)
  return {
    startDate: formatDateForApi(start),
    endDate: formatDateForApi(end),
  }
}

export function daysBetween(startDate: string, endDate: string): number {
  const start = parseISO(startDate)
  const end = parseISO(endDate)
  const diffMs = end.getTime() - start.getTime()
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24))
}

export function getBrowserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}
