import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { CreateExerciseForm } from '../exercises/CreateExerciseForm'

describe('CreateExerciseForm', () => {
  it('shows global availability notice for coach/admin create flows', () => {
    render(
      <CreateExerciseForm
        onSubmit={vi.fn()}
        submitLabel="Create exercise"
      />,
    )

    expect(
      screen.getByText(/Exercises added here are available to every client and coach/i),
    ).toBeInTheDocument()
  })
})
