import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  formatDateTimeLocalInTimezone,
  parseDateTimeLocalInTimezone,
} from './date'
import { getTimezoneOptions } from './timezones'

describe('timezone date helpers', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-05T21:56:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('formats datetime-local values in the user timezone', () => {
    expect(formatDateTimeLocalInTimezone(new Date(), 'America/Los_Angeles')).toBe(
      '2026-07-05T14:56',
    )
  })

  it('parses datetime-local values as wall clock in the user timezone', () => {
    expect(parseDateTimeLocalInTimezone('2026-07-05T14:56', 'America/Los_Angeles')).toBe(
      '2026-07-05T21:56:00.000Z',
    )
  })
})

describe('getTimezoneOptions', () => {
  it('includes the current value when it is not in the supported list', () => {
    const options = getTimezoneOptions('Legacy/Timezone')
    expect(options[0]).toEqual({
      value: 'Legacy/Timezone',
      label: 'Legacy/Timezone',
    })
  })

  it('returns timezone options with labels', () => {
    const options = getTimezoneOptions()
    expect(options.length).toBeGreaterThan(0)
    expect(options[0]?.label).toMatch(/\(GMT/)
  })
})
