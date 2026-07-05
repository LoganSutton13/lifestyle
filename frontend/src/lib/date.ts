import { format, parseISO, subMonths } from 'date-fns'
import { formatInTimeZone, fromZonedTime } from 'date-fns-tz'

export function formatDateForApi(date: Date): string {
  return format(date, 'yyyy-MM-dd')
}

export function formatDateForApiInTimezone(date: Date, timezone: string): string {
  return formatInTimeZone(date, timezone, 'yyyy-MM-dd')
}

export function formatDateTimeForApi(date: Date): string {
  return date.toISOString()
}

export function formatDateTimeLocalInTimezone(date: Date, timezone: string): string {
  return formatInTimeZone(date, timezone, "yyyy-MM-dd'T'HH:mm")
}

export function parseDateTimeLocalInTimezone(value: string, timezone: string): string {
  return fromZonedTime(value, timezone).toISOString()
}

export function formatDisplayDate(dateStr: string): string {
  return format(parseISO(dateStr), 'MMM d, yyyy')
}

export function formatDisplayDateInTimezone(dateStr: string, timezone: string): string {
  return formatInTimeZone(parseISO(dateStr), timezone, 'MMM d, yyyy')
}

export function formatDisplayDateTime(dateStr: string): string {
  return format(parseISO(dateStr), 'MMM d, yyyy h:mm a')
}

export function formatDisplayDateTimeInTimezone(dateStr: string, timezone: string): string {
  return formatInTimeZone(parseISO(dateStr), timezone, 'MMM d, yyyy h:mm a')
}

export function getTodayDateString(): string {
  return format(new Date(), 'yyyy-MM-dd')
}

export function getTodayDateStringInTimezone(timezone: string): string {
  return formatInTimeZone(new Date(), timezone, 'yyyy-MM-dd')
}

export function getDefaultMeasurementRange(timezone?: string): { startDate: string; endDate: string } {
  const end = new Date()
  const start = subMonths(end, 1)
  if (timezone) {
    return {
      startDate: formatDateForApiInTimezone(start, timezone),
      endDate: formatDateForApiInTimezone(end, timezone),
    }
  }
  return {
    startDate: formatDateForApi(start),
    endDate: formatDateForApi(end),
  }
}

export function getRangeFromPreset(months: number, timezone?: string): { startDate: string; endDate: string } {
  const end = new Date()
  const start = subMonths(end, months)
  if (timezone) {
    return {
      startDate: formatDateForApiInTimezone(start, timezone),
      endDate: formatDateForApiInTimezone(end, timezone),
    }
  }
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
