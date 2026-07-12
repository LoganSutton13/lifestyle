import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { EndWorkoutSheet } from './EndWorkoutSheet'
import type { WorkoutSession } from './types'

const baseSession: WorkoutSession = {
  id: 'session-1',
  source: 'freestyle',
  status: 'in_progress',
  title: null,
  startedAt: new Date().toISOString(),
  completedAt: null,
  notes: '',
  assignment: null,
  exercises: [],
}

describe('EndWorkoutSheet', () => {
  it('warns about incomplete sets and blocks finish with zero completed sets', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    const session: WorkoutSession = {
      ...baseSession,
      exercises: [
        {
          id: 'se-1',
          position: 0,
          isUnilateral: false,
          restSeconds: 90,
          notes: '',
          exercise: {
            id: 'ex-1',
            name: 'Squat',
            trackingType: 'reps_load',
            equipment: { key: 'barbell', displayName: 'Barbell' },
          },
          prescription: null,
          sets: [
            {
              id: 'set-1',
              position: 0,
              setType: 'normal',
              reps: 5,
              loadValue: '185',
              loadUnitKey: 'lb',
              durationSeconds: null,
              rpe: null,
              completedAt: null,
            },
          ],
        },
      ],
    }

    render(
      <EndWorkoutSheet
        open
        session={session}
        onClose={() => undefined}
        onConfirm={onConfirm}
      />,
    )

    expect(
      screen.getByText(/This workout contains incomplete sets/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/Complete at least one set/i)).toBeInTheDocument()
    const finish = screen.getByRole('button', { name: /Discard Incomplete Sets and Finish/i })
    expect(finish).toBeDisabled()
    await user.click(finish)
    expect(onConfirm).not.toHaveBeenCalled()
  })
})
