import { describe, expect, it } from 'vitest'
import { hasSetFieldErrors, validateSetForCompletion } from './helpers'

describe('set completion validation', () => {
  it('requires load and reps for reps_load', () => {
    const errors = validateSetForCompletion('reps_load', {
      reps: null,
      loadValue: null,
      loadUnitKey: null,
      durationSeconds: null,
    })
    expect(hasSetFieldErrors(errors)).toBe(true)
    expect(errors.reps).toBeTruthy()
    expect(errors.loadValue).toBeTruthy()
  })

  it('requires duration for duration tracking', () => {
    const errors = validateSetForCompletion('duration', {
      reps: null,
      loadValue: null,
      loadUnitKey: null,
      durationSeconds: null,
    })
    expect(errors.durationSeconds).toBeTruthy()
  })

  it('passes when required fields are present', () => {
    const errors = validateSetForCompletion('reps_only', {
      reps: 10,
      loadValue: null,
      loadUnitKey: null,
      durationSeconds: null,
    })
    expect(hasSetFieldErrors(errors)).toBe(false)
  })
})
