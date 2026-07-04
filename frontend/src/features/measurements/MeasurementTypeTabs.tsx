import { cn } from '../../lib/cn'
import type { MeasurementType } from './api'

export interface MeasurementTypeTabsProps {
  types: MeasurementType[]
  value: string
  onChange: (typeKey: string) => void
}

export function MeasurementTypeTabs({ types, value, onChange }: MeasurementTypeTabsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Measurement types">
      {types.map((type) => (
        <button
          key={type.key}
          type="button"
          role="tab"
          aria-selected={value === type.key}
          onClick={() => onChange(type.key)}
          className={cn(
            'min-h-touch shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-colors',
            value === type.key
              ? 'bg-primary text-white'
              : 'bg-surface text-textMuted hover:bg-primarySoft hover:text-primaryDark',
          )}
        >
          {type.displayName}
        </button>
      ))}
    </div>
  )
}
