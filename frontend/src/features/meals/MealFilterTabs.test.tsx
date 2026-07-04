import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MealFilterTabs } from './MealFilterTabs'

describe('MealFilterTabs', () => {
  it('calls onChange with category and supports all filters', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(<MealFilterTabs value="all" onChange={onChange} />)

    expect(screen.getByRole('tab', { name: 'All' })).toHaveAttribute('aria-selected', 'true')

    await user.click(screen.getByRole('tab', { name: 'Breakfast' }))
    expect(onChange).toHaveBeenCalledWith('breakfast')

    await user.click(screen.getByRole('tab', { name: 'Dinner' }))
    expect(onChange).toHaveBeenCalledWith('dinner')
  })
})
