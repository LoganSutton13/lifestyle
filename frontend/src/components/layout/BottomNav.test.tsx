import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { BottomNav } from './BottomNav'

describe('BottomNav', () => {
  it('renders five client tabs with labels', () => {
    render(
      <MemoryRouter initialEntries={['/app/meals']}>
        <BottomNav />
      </MemoryRouter>,
    )

    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument()
    expect(screen.getByText('Meals')).toBeInTheDocument()
    expect(screen.getByText('Checklist')).toBeInTheDocument()
    expect(screen.getByText('Workout')).toBeInTheDocument()
    expect(screen.getByText('Data')).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getAllByRole('link')).toHaveLength(5)
  })

  it('marks the Workout tab active for nested workout routes', () => {
    render(
      <MemoryRouter initialEntries={['/app/workouts/active/session-1']}>
        <BottomNav />
      </MemoryRouter>,
    )

    const workoutLink = screen.getByText('Workout').closest('a')
    expect(workoutLink).toHaveClass('text-primary')
  })
})
