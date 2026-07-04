import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthGuard } from './AuthGuard'

vi.mock('./hooks', () => ({
  useAuthUser: vi.fn(),
  useAuthBootstrap: vi.fn(),
  hasRole: vi.fn(),
}))

import { useAuthBootstrap, useAuthUser } from './hooks'

describe('AuthGuard', () => {
  it('redirects unauthenticated users to login', () => {
    vi.mocked(useAuthUser).mockReturnValue(null)
    vi.mocked(useAuthBootstrap).mockReturnValue({
      isLoading: false,
      isError: true,
      data: null,
    } as ReturnType<typeof useAuthBootstrap>)

    render(
      <MemoryRouter initialEntries={['/app/meals']}>
        <Routes>
          <Route element={<AuthGuard roles={['client']} />}>
            <Route path="/app/meals" element={<div>Meals</div>} />
          </Route>
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })
})
