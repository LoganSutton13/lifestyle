import { apiRequest } from '../../../lib/apiClient'
import type {
  AssignmentListItem,
  AssignmentListResponse,
  WorkoutHistoryListResponse,
  WorkoutSession,
} from '../../workouts/types'
import type {
  AssignmentCreateRequest,
  TemplateDetail,
  TemplateDraftUpdateRequest,
  TemplateListResponse,
  TemplateVersion,
} from './types'

export function fetchWorkoutTemplates(includeArchived = false): Promise<TemplateListResponse> {
  const search = new URLSearchParams()
  if (includeArchived) {
    search.set('includeArchived', 'true')
  }
  const suffix = search.toString() ? `?${search.toString()}` : ''
  return apiRequest<TemplateListResponse>(`/api/coach/workout-templates${suffix}`)
}

export function createWorkoutTemplate(body: {
  title: string
  notes?: string
}): Promise<TemplateDetail> {
  return apiRequest<TemplateDetail>('/api/coach/workout-templates', {
    method: 'POST',
    body,
  })
}

export function fetchWorkoutTemplate(templateId: string): Promise<TemplateDetail> {
  return apiRequest<TemplateDetail>(`/api/coach/workout-templates/${templateId}`)
}

export function archiveWorkoutTemplate(templateId: string): Promise<void> {
  return apiRequest<void>(`/api/coach/workout-templates/${templateId}`, {
    method: 'DELETE',
  })
}

export function createTemplateDraft(templateId: string): Promise<TemplateVersion> {
  return apiRequest<TemplateVersion>(`/api/coach/workout-templates/${templateId}/draft`, {
    method: 'POST',
  })
}

export function updateTemplateDraft(
  versionId: string,
  body: TemplateDraftUpdateRequest,
): Promise<TemplateVersion> {
  return apiRequest<TemplateVersion>(`/api/coach/workout-template-versions/${versionId}`, {
    method: 'PUT',
    body,
  })
}

export function publishTemplateVersion(versionId: string): Promise<TemplateVersion> {
  return apiRequest<TemplateVersion>(`/api/coach/workout-template-versions/${versionId}/publish`, {
    method: 'POST',
  })
}

export function fetchClientAssignments(
  clientId: string,
  params: { cursor?: string | null; pageSize?: number } = {},
): Promise<AssignmentListResponse> {
  const search = new URLSearchParams()
  search.set('pageSize', String(params.pageSize ?? 20))
  if (params.cursor) search.set('cursor', params.cursor)
  return apiRequest<AssignmentListResponse>(
    `/api/coach/clients/${clientId}/workout-assignments?${search.toString()}`,
  )
}

export function createClientAssignment(
  clientId: string,
  body: AssignmentCreateRequest,
): Promise<AssignmentListItem> {
  return apiRequest<AssignmentListItem>(`/api/coach/clients/${clientId}/workout-assignments`, {
    method: 'POST',
    body,
  })
}

export function cancelClientAssignment(clientId: string, assignmentId: string): Promise<void> {
  return apiRequest<void>(
    `/api/coach/clients/${clientId}/workout-assignments/${assignmentId}/cancel`,
    { method: 'POST' },
  )
}

export function fetchClientWorkoutHistory(
  clientId: string,
  params: { cursor?: string | null; pageSize?: number } = {},
): Promise<WorkoutHistoryListResponse> {
  const search = new URLSearchParams()
  search.set('pageSize', String(params.pageSize ?? 20))
  if (params.cursor) search.set('cursor', params.cursor)
  return apiRequest<WorkoutHistoryListResponse>(
    `/api/coach/clients/${clientId}/workouts?${search.toString()}`,
  )
}

export function fetchClientWorkoutDetail(
  clientId: string,
  sessionId: string,
): Promise<WorkoutSession> {
  return apiRequest<WorkoutSession>(`/api/coach/clients/${clientId}/workouts/${sessionId}`)
}
