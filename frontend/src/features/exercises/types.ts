export type TrackingType = 'reps_load' | 'reps_only' | 'duration'

export interface EquipmentInfo {
  key: string
  displayName: string
}

export interface MuscleGroupInfo {
  key: string
  displayName: string
}

export interface Exercise {
  id: string
  name: string
  slug: string
  equipment: EquipmentInfo
  trackingType: TrackingType
  defaultUnilateral: boolean
  defaultRestSeconds: number
  instructions: string
  primaryMuscles: MuscleGroupInfo[]
  secondaryMuscles: MuscleGroupInfo[]
  archivedAt: string | null
  createdByUserId: string | null
}

export interface ExerciseListResponse {
  items: Exercise[]
  nextCursor: string | null
}

export interface ExerciseSuggestionsResponse {
  items: Exercise[]
}

export interface ExerciseSearchParams {
  query?: string
  equipment?: string
  muscleGroup?: string
  includeArchived?: boolean
  pageSize?: number
  cursor?: string | null
}

export interface ExerciseCreateRequest {
  name: string
  equipmentKey: string
  trackingType: TrackingType
  defaultUnilateral?: boolean
  defaultRestSeconds?: number
  primaryMuscleKeys: string[]
  secondaryMuscleKeys?: string[]
  instructions?: string
}

export interface ExerciseUpdateRequest {
  name?: string
  equipmentKey?: string
  trackingType?: TrackingType
  defaultUnilateral?: boolean
  defaultRestSeconds?: number
  primaryMuscleKeys?: string[]
  secondaryMuscleKeys?: string[]
  instructions?: string
}

export const EQUIPMENT_OPTIONS: EquipmentInfo[] = [
  { key: 'barbell', displayName: 'Barbell' },
  { key: 'dumbbell', displayName: 'Dumbbell' },
  { key: 'machine', displayName: 'Machine' },
  { key: 'cable', displayName: 'Cable' },
  { key: 'bodyweight', displayName: 'Bodyweight' },
  { key: 'kettlebell', displayName: 'Kettlebell' },
  { key: 'band', displayName: 'Band' },
  { key: 'other', displayName: 'Other' },
]

export const MUSCLE_GROUP_OPTIONS: MuscleGroupInfo[] = [
  { key: 'chest', displayName: 'Chest' },
  { key: 'back', displayName: 'Back' },
  { key: 'shoulders', displayName: 'Shoulders' },
  { key: 'biceps', displayName: 'Biceps' },
  { key: 'triceps', displayName: 'Triceps' },
  { key: 'forearms', displayName: 'Forearms' },
  { key: 'quadriceps', displayName: 'Quadriceps' },
  { key: 'hamstrings', displayName: 'Hamstrings' },
  { key: 'glutes', displayName: 'Glutes' },
  { key: 'calves', displayName: 'Calves' },
  { key: 'core', displayName: 'Core' },
  { key: 'full_body', displayName: 'Full Body' },
]

export function trackingTypeLabel(trackingType: TrackingType): string {
  switch (trackingType) {
    case 'reps_load':
      return 'Reps & Load'
    case 'reps_only':
      return 'Reps'
    case 'duration':
      return 'Duration'
    default:
      return trackingType
  }
}
