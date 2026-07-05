import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AddMeasurementModal } from './AddMeasurementModal'
const types = [
  { key: 'body_weight', displayName: 'Body Weight' },
  { key: 'waist', displayName: 'Waist' },
]

describe('AddMeasurementModal', () => {
  it('defaults recordedAt to the user timezone wall clock', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-05T21:56:00Z'))

    render(
      <AddMeasurementModal
        open
        onClose={() => undefined}
        types={types}
        defaultTypeKey="body_weight"
        timezone="America/Los_Angeles"
        onSubmit={() => undefined}
      />,
    )

    expect(screen.getByLabelText('Recorded at')).toHaveValue('2026-07-05T14:56')
    vi.useRealTimers()
  })

  it('validates numeric value must be greater than zero', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(
      <AddMeasurementModal
        open
        onClose={() => undefined}
        types={types}
        defaultTypeKey="body_weight"
        timezone="America/Los_Angeles"
        onSubmit={onSubmit}
      />,
    )

    await user.clear(screen.getByLabelText('Value'))
    await user.type(screen.getByLabelText('Value'), '0')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('Value must be greater than zero')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits valid measurement values', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(
      <AddMeasurementModal
        open
        onClose={() => undefined}
        types={types}
        defaultTypeKey="body_weight"
        timezone="America/Los_Angeles"
        onSubmit={onSubmit}
      />,
    )

    await user.clear(screen.getByLabelText('Value'))
    await user.type(screen.getByLabelText('Value'), '183.2')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalled())
  })
})
