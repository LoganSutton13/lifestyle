import { MEAL_CATEGORIES, type MealCategoryKey } from '../../lib/constants'
import { PillTabs } from '../../components/ui/PillTabs'

export interface MealFilterTabsProps {
  value: MealCategoryKey
  onChange: (category: MealCategoryKey) => void
}

export function MealFilterTabs({ value, onChange }: MealFilterTabsProps) {
  return (
    <PillTabs
      options={MEAL_CATEGORIES.map((category) => ({
        value: category.key,
        label: category.label,
      }))}
      value={value}
      onChange={onChange}
      ariaLabel="Meal categories"
      layout="scroll"
    />
  )
}
