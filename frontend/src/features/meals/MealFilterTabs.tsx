import { cn, MEAL_CATEGORIES, type MealCategoryKey } from '../../lib/constants'

export interface MealFilterTabsProps {
  value: MealCategoryKey
  onChange: (category: MealCategoryKey) => void
}

export function MealFilterTabs({ value, onChange }: MealFilterTabsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Meal categories">
      {MEAL_CATEGORIES.map((category) => (
        <button
          key={category.key}
          type="button"
          role="tab"
          aria-selected={value === category.key}
          onClick={() => onChange(category.key)}
          className={cn(
            'min-h-touch shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-colors',
            value === category.key
              ? 'bg-primary text-white'
              : 'bg-surface text-textMuted hover:bg-primarySoft hover:text-primaryDark',
          )}
        >
          {category.label}
        </button>
      ))}
    </div>
  )
}
