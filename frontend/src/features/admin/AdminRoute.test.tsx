import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthGuard } from '../auth/AuthGuard'

vi.mock('../auth/hooks', () => ({
  useAuthUser: vi.fn(),
  useAuthBootstrap: vi.fn(),
  hasRole: (user: { role: string } | null, roles: string[]) =>
    !!user && roles.includes(user.role),
}))

import { useAuthBootstrap, useAuthUser } from '../auth/hooks'

describe('Admin route rejection', () => {
  it('rejects non-admin user from admin routes', () => {
    vi.mocked(useAuthUser).mockReturnValue({
      id: '1',
      username: 'client1',
      firstName: 'Client',
      lastName: 'User',
      role: 'client',
      avatarKey: 'apple',
      timezone: 'UTC',
    })
    vi.mocked(useAuthBootstrap).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        id: '1',
        username: 'client1',
        firstName: 'Client',
        lastName: 'User',
        role: 'client',
        avatarKey: 'apple',
        timezone: 'UTC',
      },
    } as ReturnType<typeof useAuthBootstrap>)

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<AuthGuard roles={['admin']} redirectTo="/admin/login" />}>
            <Route path="/admin" element={<div>Admin Dashboard</div>} />
          </Route>
          <Route path="/app/checklist" element={<div>Client Checklist</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Client Checklist')).toBeInTheDocument()
    expect(screen.queryByText('Admin Dashboard')).not.toBeInTheDocument()
  })
})
