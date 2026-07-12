import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeAll, describe, expect, it, vi } from 'vitest'
import { ExercisePager } from './ExercisePager'

beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

describe('ExercisePager', () => {
  it('orders pages and updates active page via indicator controls', async () => {
    const user = userEvent.setup()
    const onActiveChange = vi.fn()

    render(
      <ExercisePager
        activeId="a"
        onActiveChange={onActiveChange}
        pages={[
          { id: 'a', label: 'Exercise 1', content: <div>One</div> },
          { id: 'b', label: 'Exercise 2', content: <div>Two</div> },
          { id: 'add', label: 'Add exercise', content: <div>Add</div> },
        ]}
      />,
    )

    expect(screen.getByText('One')).toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: 'Exercise 2' }))
    expect(onActiveChange).toHaveBeenCalledWith('b')
  })
})
