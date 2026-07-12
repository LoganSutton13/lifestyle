import { Search } from 'lucide-react'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { EQUIPMENT_OPTIONS, MUSCLE_GROUP_OPTIONS } from './types'

export interface ExerciseSearchFiltersProps {
  query: string
  equipment: string
  muscleGroup: string
  onQueryChange: (value: string) => void
  onEquipmentChange: (value: string) => void
  onMuscleGroupChange: (value: string) => void
}

export function ExerciseSearchFilters({
  query,
  equipment,
  muscleGroup,
  onQueryChange,
  onEquipmentChange,
  onMuscleGroupChange,
}: ExerciseSearchFiltersProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-textMuted"
          aria-hidden="true"
        />
        <Input
          aria-label="Search exercises"
          placeholder="Search exercises..."
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          className="pl-9"
        />
      </div>
      <div className="flex gap-3">
        <Select
          aria-label="Filter by equipment"
          className="flex-1"
          value={equipment}
          onChange={(event) => onEquipmentChange(event.target.value)}
          options={[
            { value: '', label: 'All equipment' },
            ...EQUIPMENT_OPTIONS.map((option) => ({ value: option.key, label: option.displayName })),
          ]}
        />
        <Select
          aria-label="Filter by muscle group"
          className="flex-1"
          value={muscleGroup}
          onChange={(event) => onMuscleGroupChange(event.target.value)}
          options={[
            { value: '', label: 'All muscles' },
            ...MUSCLE_GROUP_OPTIONS.map((option) => ({ value: option.key, label: option.displayName })),
          ]}
        />
      </div>
    </div>
  )
}
