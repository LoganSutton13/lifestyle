import { cn } from '../../lib/cn'

export interface PillTabOption<T extends string = string> {
  value: T
  label: string
}

export interface PillTabsProps<T extends string = string> {
  options: PillTabOption<T>[]
  value: T
  onChange: (value: T) => void
  ariaLabel: string
  layout?: 'scroll' | 'wrap'
  className?: string
}

export function PillTabs<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
  layout = 'scroll',
  className,
}: PillTabsProps<T>) {
  const isScroll = layout === 'scroll'

  return (
    <div
      className={cn('flex gap-2', isScroll ? 'overflow-x-auto pb-1' : 'flex-wrap', className)}
      role={isScroll ? 'tablist' : 'group'}
      aria-label={ariaLabel}
    >
      {options.map((option) => {
        const selected = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            role={isScroll ? 'tab' : undefined}
            aria-selected={isScroll ? selected : undefined}
            onClick={() => onChange(option.value)}
            className={cn(
              'min-h-touch rounded-full py-2 text-sm font-medium transition-colors',
              isScroll ? 'shrink-0 px-4' : 'px-3',
              selected
                ? 'bg-primary text-white'
                : 'bg-surface text-textMuted hover:bg-primarySoft hover:text-primaryDark',
            )}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
