import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../../components/ui/Toast'
import * as workoutsApi from './api'
import { WorkoutsPage } from './WorkoutsPage'
import type { WorkoutSession } from './types'

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <MemoryRouter>
          <WorkoutsPage />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

const activeSession: WorkoutSession = {
  id: 'session-1',
  source: 'freestyle',
  status: 'in_progress',
  title: null,
  startedAt: new Date().toISOString(),
  completedAt: null,
  notes: '',
  assignment: null,
  exercises: [
    {
      id: 'se-1',
      position: 0,
      isUnilateral: false,
      restSeconds: 90,
      notes: '',
      exercise: {
        id: 'ex-1',
        name: 'Bench Press',
        trackingType: 'reps_load',
        equipment: { key: 'barbell', displayName: 'Barbell' },
      },
      prescription: null,
      sets: [
        {
          id: 'set-1',
          position: 0,
          setType: 'normal',
          reps: 10,
          loadValue: '135',
          loadUnitKey: 'lb',
          durationSeconds: null,
          rpe: null,
          completedAt: new Date().toISOString(),
        },
      ],
    },
  ],
}

describe('WorkoutsPage', () => {
  it('shows Resume when an active session exists and hides freestyle start as primary', async () => {
    vi.spyOn(workoutsApi, 'fetchActiveWorkout').mockResolvedValue({ session: activeSession })
    vi.spyOn(workoutsApi, 'fetchAssignments').mockResolvedValue({ items: [], nextCursor: null })
    vi.spyOn(workoutsApi, 'fetchWorkoutHistory').mockResolvedValue({ items: [], nextCursor: null })

    renderPage()

    expect(await screen.findByRole('button', { name: /Resume Workout/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Start Freestyle Workout/i })).not.toBeInTheDocument()
    expect(screen.getByText(/Finish or discard your active workout/i)).toBeInTheDocument()
  })

  it('starts a freestyle workout', async () => {
    const user = userEvent.setup()
    vi.spyOn(workoutsApi, 'fetchActiveWorkout').mockResolvedValue({ session: null })
    vi.spyOn(workoutsApi, 'fetchAssignments').mockResolvedValue({ items: [], nextCursor: null })
    vi.spyOn(workoutsApi, 'fetchWorkoutHistory').mockResolvedValue({ items: [], nextCursor: null })
    const startSpy = vi.spyOn(workoutsApi, 'startWorkout').mockResolvedValue({
      ...activeSession,
      exercises: [],
    })

    renderPage()

    await user.click(await screen.findByRole('button', { name: /Start Freestyle Workout/i }))

    await waitFor(() => expect(startSpy).toHaveBeenCalled())
    expect(startSpy.mock.calls[0]?.[0]).toEqual({ mode: 'freestyle' })
  })
})
