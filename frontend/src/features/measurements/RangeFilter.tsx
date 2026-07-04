import { cn, RANGE_PRESETS, type RangePresetKey } from '../../lib/constants'

export interface RangeFilterProps {
  value: RangePresetKey
  onChange: (preset: RangePresetKey) => void
}

export function RangeFilter({ value, onChange }: RangeFilterProps) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Time range">
      {RANGE_PRESETS.map((preset) => (
        <button
          key={preset.key}
          type="button"
          onClick={() => onChange(preset.key)}
          className={cn(
            'min-h-touch rounded-full px-3 py-2 text-sm font-medium transition-colors',
            value === preset.key
              ? 'bg-primary text-white'
              : 'bg-surface text-textMuted hover:bg-primarySoft hover:text-primaryDark',
          )}
        >
          {preset.label}
        </button>
      ))}
    </div>
  )
}
