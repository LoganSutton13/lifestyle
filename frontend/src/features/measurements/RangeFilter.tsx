import { RANGE_PRESETS, type RangePresetKey } from '../../lib/constants'
import { PillTabs } from '../../components/ui/PillTabs'

export interface RangeFilterProps {
  value: RangePresetKey
  onChange: (preset: RangePresetKey) => void
}

export function RangeFilter({ value, onChange }: RangeFilterProps) {
  return (
    <PillTabs
      options={RANGE_PRESETS.map((preset) => ({
        value: preset.key,
        label: preset.label,
      }))}
      value={value}
      onChange={onChange}
      ariaLabel="Time range"
      layout="wrap"
    />
  )
}
