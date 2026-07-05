import type { SelectOption } from '../components/ui/Select'

const FALLBACK_TIMEZONES = [
  'UTC',
  'America/Los_Angeles',
  'America/Denver',
  'America/Chicago',
  'America/New_York',
  'Europe/London',
  'Europe/Paris',
  'Asia/Tokyo',
  'Australia/Sydney',
]

function getSupportedTimezones(): string[] {
  if (typeof Intl.supportedValuesOf === 'function') {
    return Intl.supportedValuesOf('timeZone')
  }
  return FALLBACK_TIMEZONES
}

function getTimezoneOffsetMinutes(timezone: string, date: Date): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    timeZoneName: 'shortOffset',
  }).formatToParts(date)
  const offsetPart = parts.find((part) => part.type === 'timeZoneName')?.value ?? 'GMT'
  const match = offsetPart.match(/GMT([+-])(\d{1,2})(?::(\d{2}))?/)
  if (!match) {
    return 0
  }
  const sign = match[1] === '-' ? -1 : 1
  const hours = Number(match[2])
  const minutes = Number(match[3] ?? '0')
  return sign * (hours * 60 + minutes)
}

function formatTimezoneLabel(timezone: string, date: Date): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    timeZoneName: 'shortOffset',
  }).formatToParts(date)
  const offset = parts.find((part) => part.type === 'timeZoneName')?.value ?? 'GMT'
  return `(${offset}) ${timezone}`
}

export function getTimezoneOptions(currentValue?: string): SelectOption[] {
  const now = new Date()
  const timezones = getSupportedTimezones()
  const options = timezones
    .map((timezone) => ({
      value: timezone,
      label: formatTimezoneLabel(timezone, now),
      offset: getTimezoneOffsetMinutes(timezone, now),
    }))
    .sort((a, b) => a.offset - b.offset || a.value.localeCompare(b.value))
    .map(({ value, label }) => ({ value, label }))

  if (currentValue && !timezones.includes(currentValue)) {
    options.unshift({
      value: currentValue,
      label: currentValue,
    })
  }

  return options
}
