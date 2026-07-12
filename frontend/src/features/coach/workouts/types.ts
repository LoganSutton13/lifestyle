export type TemplateVersionStatus = 'draft' | 'published'

export interface TemplateSet {
  id: string
  position: number
  setType: string
  targetRepsMin: number | null
  targetRepsMax: number | null
  targetLoadValue: string | null
  targetLoadUnitKey: string | null
  targetDurationSeconds: number | null
  targetRpe: string | null
  notes: string
}

export interface TemplateExercise {
  id: string
  position: number
  exerciseId: string
  exerciseName: string
  isUnilateral: boolean
  restSeconds: number
  notes: string
  sets: TemplateSet[]
}

export interface TemplateVersion {
  id: string
  versionNumber: number
  title: string
  notes: string
  status: TemplateVersionStatus | string
  createdAt: string
  publishedAt: string | null
  exercises: TemplateExercise[]
}

export interface TemplateListItem {
  id: string
  archivedAt: string | null
  updatedAt: string
  title: string
  hasDraft: boolean
  latestPublishedVersionNumber: number | null
}

export interface TemplateListResponse {
  items: TemplateListItem[]
}

export interface TemplateDetail {
  id: string
  coachId: string
  archivedAt: string | null
  versions: TemplateVersion[]
}

export interface TemplateSetInput {
  position: number
  setType?: string
  targetRepsMin?: number | null
  targetRepsMax?: number | null
  targetLoadValue?: number | string | null
  targetLoadUnitKey?: string | null
  targetDurationSeconds?: number | null
  targetRpe?: number | string | null
  notes?: string
}

export interface TemplateExerciseInput {
  position: number
  exerciseId: string
  isUnilateral?: boolean
  restSeconds?: number
  notes?: string
  sets?: TemplateSetInput[]
}

export interface TemplateDraftUpdateRequest {
  title: string
  notes?: string
  exercises: TemplateExerciseInput[]
}

export interface AssignmentCreateRequest {
  templateVersionId: string
  scheduledFor?: string | null
  dueAt?: string | null
  notes?: string
}
