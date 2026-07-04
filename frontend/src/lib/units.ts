export interface UnitOption {
  key: string
  label: string
  symbol: string
}

export const WEIGHT_UNITS: UnitOption[] = [
  { key: 'lb', label: 'Pounds', symbol: 'lbs' },
  { key: 'kg', label: 'Kilograms', symbol: 'kg' },
]

export const LENGTH_UNITS: UnitOption[] = [
  { key: 'in', label: 'Inches', symbol: 'in' },
  { key: 'cm', label: 'Centimeters', symbol: 'cm' },
]

export function getDefaultUnitForType(typeKey: string): string {
  if (typeKey === 'body_weight') {
    return 'lb'
  }
  return 'in'
}

export function getUnitsForType(typeKey: string): UnitOption[] {
  if (typeKey === 'body_weight') {
    return WEIGHT_UNITS
  }
  return LENGTH_UNITS
}
