import { apiRequest } from '../../lib/apiClient'
import { COACH_PAGE_SIZE } from '../../lib/constants'
import type { MeasurementGraphResponse, MeasurementTypesResponse } from '../measurements/api'

export interface CoachClientSummary {
  id: string
  username: string
  firstName: string
  lastName: string
  avatarKey: string
  latestBodyWeight: number | null
  todayCompletedTasks: number
  todayTotalTasks: number
}

export interface CoachClientProfile {
  id: string
  username: string
  firstName: string
  lastName: string
  timezone: string
}

export interface CoachClientListResponse {
  items: CoachClientSummary[]
  page: number
  pageSize: number
  total: number
  hasNextPage: boolean
}

export interface ClientSearchResult {
  id: string
  username: string
  firstName: string
  lastName: string
  avatarKey: string
}

export interface CoachMealItem {
  id: string
  name: string
  category: string
  categoryLabel: string
  description: string
  assignedAt: string
}

export interface CoachTaskItem {
  id: string
  title: string
  description: string
  activeFrom: string
  activeUntil: string | null
  recurrenceFrequency: 'daily' | 'weekly'
  recurrenceInterval: number
  recurrenceDays: number[]
  archivedAt: string | null
}

export interface ChecklistHistoryDay {
  date: string
  totalTasks: number
  completedTasks: number
}

export interface DailyNoteItem {
  date: string
  body: string
  updatedAt: string
}

export function fetchCoachClient(clientId: string): Promise<CoachClientProfile> {
  return apiRequest<CoachClientProfile>(`/api/coach/clients/${clientId}`)
}

export function fetchCoachClients(params: {
  search?: string
  page?: number
  pageSize?: number
}): Promise<CoachClientListResponse> {
  const search = new URLSearchParams()
  search.set('page', String(params.page ?? 1))
  search.set('pageSize', String(params.pageSize ?? COACH_PAGE_SIZE))
  if (params.search) {
    search.set('search', params.search)
  }
  return apiRequest<CoachClientListResponse>(`/api/coach/clients?${search.toString()}`)
}

export function searchClients(query: string): Promise<{ items: ClientSearchResult[] }> {
  return apiRequest<{ items: ClientSearchResult[] }>(
    `/api/coach/client-search?query=${encodeURIComponent(query)}`,
  )
}

export function addClient(clientId: string): Promise<void> {
  return apiRequest<void>('/api/coach/clients', {
    method: 'POST',
    body: { clientId },
  })
}

export function removeClient(clientId: string): Promise<void> {
  return apiRequest<void>(`/api/coach/clients/${clientId}`, { method: 'DELETE' })
}

export function fetchClientMeals(
  clientId: string,
  params: { page?: number; category?: string },
): Promise<{ items: CoachMealItem[]; page: number; pageSize: number; total: number; hasNextPage: boolean }> {
  const search = new URLSearchParams()
  search.set('page', String(params.page ?? 1))
  search.set('pageSize', String(COACH_PAGE_SIZE))
  if (params.category && params.category !== 'all') {
    search.set('category', params.category)
  }
  return apiRequest(`/api/coach/clients/${clientId}/meals?${search.toString()}`)
}

export function createClientMeal(
  clientId: string,
  payload: { name: string; category: string; description: string },
): Promise<CoachMealItem> {
  return apiRequest<CoachMealItem>(`/api/coach/clients/${clientId}/meals`, {
    method: 'POST',
    body: payload,
  })
}

export function updateClientMeal(
  clientId: string,
  mealId: string,
  payload: Partial<{ name: string; category: string; description: string }>,
): Promise<CoachMealItem> {
  return apiRequest<CoachMealItem>(`/api/coach/clients/${clientId}/meals/${mealId}`, {
    method: 'PATCH',
    body: payload,
  })
}

export function deleteClientMeal(clientId: string, mealId: string): Promise<void> {
  return apiRequest<void>(`/api/coach/clients/${clientId}/meals/${mealId}`, { method: 'DELETE' })
}

export function fetchClientTasks(clientId: string): Promise<{ items: CoachTaskItem[] }> {
  return apiRequest<{ items: CoachTaskItem[] }>(`/api/coach/clients/${clientId}/tasks?active=true`)
}

export function createClientTask(
  clientId: string,
  payload: {
    title: string
    description?: string
    activeFrom: string
    activeUntil?: string | null
    recurrenceFrequency?: 'daily' | 'weekly'
    recurrenceInterval?: number
    recurrenceDays?: number[]
  },
): Promise<CoachTaskItem> {
  return apiRequest<CoachTaskItem>(`/api/coach/clients/${clientId}/tasks`, {
    method: 'POST',
    body: payload,
  })
}

export function updateClientTask(
  clientId: string,
  taskId: string,
  payload: Partial<{
    title: string
    description: string
    activeFrom: string
    activeUntil: string | null
    recurrenceFrequency: 'daily' | 'weekly'
    recurrenceInterval: number
    recurrenceDays: number[]
  }>,
): Promise<CoachTaskItem> {
  return apiRequest<CoachTaskItem>(`/api/coach/clients/${clientId}/tasks/${taskId}`, {
    method: 'PATCH',
    body: payload,
  })
}

export function deleteClientTask(clientId: string, taskId: string): Promise<void> {
  return apiRequest<void>(`/api/coach/clients/${clientId}/tasks/${taskId}`, { method: 'DELETE' })
}

export function fetchClientMeasurementTypes(clientId: string): Promise<MeasurementTypesResponse> {
  return apiRequest<MeasurementTypesResponse>(`/api/coach/clients/${clientId}/measurement-types`)
}

export function fetchClientMeasurements(
  clientId: string,
  params: { typeKey: string; startDate: string; endDate: string; unitKey: string },
): Promise<MeasurementGraphResponse> {
  const search = new URLSearchParams(params)
  return apiRequest<MeasurementGraphResponse>(
    `/api/coach/clients/${clientId}/measurements?${search.toString()}`,
  )
}

export function fetchChecklistHistory(
  clientId: string,
  params: { startDate: string; endDate: string },
): Promise<{ items: ChecklistHistoryDay[] }> {
  const search = new URLSearchParams(params)
  return apiRequest(`/api/coach/clients/${clientId}/checklist-history?${search.toString()}`)
}

export function fetchDailyNotes(
  clientId: string,
  params: { startDate: string; endDate: string },
): Promise<{ items: DailyNoteItem[] }> {
  const search = new URLSearchParams(params)
  return apiRequest(`/api/coach/clients/${clientId}/daily-notes?${search.toString()}`)
}
