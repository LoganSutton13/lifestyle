import { PillTabs } from '../../components/ui/PillTabs'
import type { MeasurementType } from './api'

export interface MeasurementTypeTabsProps {
  types: MeasurementType[]
  value: string
  onChange: (typeKey: string) => void
}

export function MeasurementTypeTabs({ types, value, onChange }: MeasurementTypeTabsProps) {
  return (
    <PillTabs
      options={types.map((type) => ({
        value: type.key,
        label: type.displayName,
      }))}
      value={value}
      onChange={onChange}
      ariaLabel="Measurement types"
      layout="scroll"
    />
  )
}
