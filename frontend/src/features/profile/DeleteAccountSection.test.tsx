import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../../components/ui/Toast'
import { DeleteAccountSection } from './DeleteAccountSection'

describe('DeleteAccountSection', () => {
  it('requires password before delete', async () => {
    const user = userEvent.setup()
    const onDelete = vi.fn()

    render(
      <ToastProvider>
        <DeleteAccountSection onDelete={onDelete} />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Delete my account' }))

    expect(await screen.findByText('Password is required')).toBeInTheDocument()
    expect(onDelete).not.toHaveBeenCalled()
  })
})
