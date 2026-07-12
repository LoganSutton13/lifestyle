import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../../components/ui/Toast'
import * as workoutsApi from './api'
import { WorkoutHistoryDetailPage } from './WorkoutHistoryDetailPage'
import type { WorkoutSession } from './types'

const completed: WorkoutSession = {
  id: 'session-1',
  source: 'freestyle',
  status: 'completed',
  title: 'Morning lift',
  startedAt: '2026-07-11T10:00:00.000Z',
  completedAt: '2026-07-11T10:45:00.000Z',
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
        name: 'Deadlift',
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
          loadValue: '225',
          loadUnitKey: 'lb',
          durationSeconds: null,
          rpe: null,
          completedAt: '2026-07-11T10:10:00.000Z',
        },
      ],
    },
  ],
}

describe('WorkoutHistoryDetailPage', () => {
  it('is read-only with no mutation controls', async () => {
    vi.spyOn(workoutsApi, 'fetchWorkoutSession').mockResolvedValue(completed)
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <MemoryRouter initialEntries={['/app/workouts/history/session-1']}>
            <Routes>
              <Route path="/app/workouts/history/:sessionId" element={<WorkoutHistoryDetailPage />} />
            </Routes>
          </MemoryRouter>
        </ToastProvider>
      </QueryClientProvider>,
    )

    expect(await screen.findByText('Morning lift')).toBeInTheDocument()
    expect(screen.getByText('Deadlift')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Complete/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Add Set/i })).not.toBeInTheDocument()
  })
})
