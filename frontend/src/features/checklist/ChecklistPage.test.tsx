import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../../components/ui/Toast'
import * as checklistApi from './api'
import { ChecklistPage } from './ChecklistPage'

vi.mock('canvas-confetti', () => ({ default: vi.fn() }))

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <ChecklistPage />
      </ToastProvider>
    </QueryClientProvider>,
  )
}

describe('ChecklistPage', () => {
  it('triggers completion mutation when checkbox changes', async () => {
    const user = userEvent.setup()
    const updateSpy = vi.spyOn(checklistApi, 'updateTaskCompletion').mockResolvedValue()

    vi.spyOn(checklistApi, 'fetchChecklist').mockResolvedValue({
      date: '2026-07-04',
      tasks: [
        {
          id: 'task-1',
          title: 'Drink water',
          description: 'Stay hydrated',
          completed: false,
        },
      ],
      note: { body: '', updatedAt: null },
    })

    renderPage()

    expect(await screen.findByText('Drink water')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Mark Drink water complete/i }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith('task-1', {
        date: expect.any(String),
        completed: true,
      }),
    )
  })
})
