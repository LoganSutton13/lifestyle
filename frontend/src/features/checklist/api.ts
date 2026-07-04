import { apiRequest } from '../../lib/apiClient'

export interface ChecklistTask {
  id: string
  title: string
  description: string
  completed: boolean
}

export interface DailyNoteInfo {
  body: string
  updatedAt: string | null
}

export interface ChecklistResponse {
  date: string
  tasks: ChecklistTask[]
  note: DailyNoteInfo
}

export function fetchChecklist(date: string): Promise<ChecklistResponse> {
  return apiRequest<ChecklistResponse>(`/api/me/checklist?date=${date}`)
}

export function updateTaskCompletion(
  taskId: string,
  payload: { date: string; completed: boolean },
): Promise<void> {
  return apiRequest<void>(`/api/me/checklist/${taskId}/completion`, {
    method: 'PATCH',
    body: payload,
  })
}

export function saveDailyNote(payload: { date: string; body: string }): Promise<void> {
  return apiRequest<void>('/api/me/daily-note', {
    method: 'PUT',
    body: payload,
  })
}
