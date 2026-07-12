import type { EquipmentInfo, TrackingType } from '../exercises/types'

export type DecimalString = string

export type SetType = 'normal' | 'warmup' | 'drop' | 'failure'
export type WorkoutSource = 'freestyle' | 'assigned'
export type WorkoutStatus = 'in_progress' | 'completed'
export type AssignmentState = 'available' | 'in_progress' | 'completed'

export interface ExerciseSummary {
  id: string
  name: string
  trackingType: TrackingType
  equipment: EquipmentInfo
}

export interface WorkoutSet {
  id: string
  position: number
  setType: SetType
  reps: number | null
  loadValue: DecimalString | null
  loadUnitKey: string | null
  durationSeconds: number | null
  rpe: DecimalString | null
  completedAt: string | null
}

export interface PrescriptionSet {
  id: string
  position: number
  setType: SetType
  targetRepsMin: number | null
  targetRepsMax: number | null
  targetLoadValue: DecimalString | null
  targetLoadUnitKey: string | null
  targetDurationSeconds: number | null
  targetRpe: DecimalString | null
}

export interface Prescription {
  notes: string
  sets: PrescriptionSet[]
}

export interface SessionExercise {
  id: string
  position: number
  isUnilateral: boolean
  restSeconds: number
  notes: string
  exercise: ExerciseSummary
  prescription: Prescription | null
  sets: WorkoutSet[]
}

export interface AssignmentRef {
  id: string
  scheduledFor: string | null
  templateVersionId: string
}

export interface WorkoutSession {
  id: string
  source: WorkoutSource
  status: WorkoutStatus
  title: string | null
  startedAt: string
  completedAt: string | null
  notes: string
  assignment: AssignmentRef | null
  exercises: SessionExercise[]
}

export interface ActiveWorkoutResponse {
  session: WorkoutSession | null
}

export interface WorkoutHistoryItem {
  id: string
  source: WorkoutSource
  title: string | null
  startedAt: string
  completedAt: string
  durationSeconds: number
  exerciseCount: number
  completedSetCount: number
}

export interface WorkoutHistoryListResponse {
  items: WorkoutHistoryItem[]
  nextCursor: string | null
}

export interface AssignmentListItem {
  id: string
  templateVersionId: string
  title: string
  coachName: string
  scheduledFor: string | null
  dueAt: string | null
  notes: string
  exerciseCount: number
  state: AssignmentState
  assignedAt: string
  sessionId: string | null
}

export interface AssignmentListResponse {
  items: AssignmentListItem[]
  nextCursor: string | null
}

export interface StartWorkoutRequest {
  mode: 'freestyle' | 'assigned'
  assignmentId?: string | null
}

export interface SessionUpdateRequest {
  title?: string | null
  notes?: string | null
}

export interface UpdateSessionExerciseRequest {
  isUnilateral?: boolean
  restSeconds?: number
  notes?: string
}

export interface AddSetRequest {
  setType?: SetType
  reps?: number | null
  loadValue?: number | string | null
  loadUnitKey?: string | null
  durationSeconds?: number | null
  rpe?: number | string | null
}

export interface UpdateSetRequest {
  setType?: SetType
  reps?: number | null
  loadValue?: number | string | null
  loadUnitKey?: string | null
  durationSeconds?: number | null
  rpe?: number | string | null
  completed?: boolean
}

export type UpdateSetPayload = UpdateSetRequest


export interface CompleteWorkoutRequest {
  discardIncompleteSets?: boolean
  notes?: string | null
}

export interface CursorPageParams {
  cursor?: string | null
  pageSize?: number
}

export const SET_TYPE_OPTIONS: { value: SetType; label: string }[] = [
  { value: 'normal', label: 'Normal' },
  { value: 'warmup', label: 'Warmup' },
  { value: 'drop', label: 'Drop' },
  { value: 'failure', label: 'Failure' },
]

export const LOAD_UNIT_OPTIONS = [
  { value: 'lb', label: 'lb' },
  { value: 'kg', label: 'kg' },
] as const
