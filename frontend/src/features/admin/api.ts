import { apiRequest } from '../../lib/apiClient'
import type { User, UserWithCreated } from '../../lib/constants'
import { COACH_PAGE_SIZE } from '../../lib/constants'

export interface AdminStats {
  clients: number
  coaches: number
  admins: number
  recentUsers: UserWithCreated[]
}

export interface AdminUserListResponse {
  items: UserWithCreated[]
  page: number
  pageSize: number
  total: number
  hasNextPage: boolean
}

export function fetchAdminStats(): Promise<AdminStats> {
  return apiRequest<AdminStats>('/api/admin/stats')
}

export function fetchAdminUsers(params: {
  role?: string
  search?: string
  page?: number
}): Promise<AdminUserListResponse> {
  const search = new URLSearchParams()
  search.set('page', String(params.page ?? 1))
  search.set('pageSize', String(COACH_PAGE_SIZE))
  if (params.role) search.set('role', params.role)
  if (params.search) search.set('search', params.search)
  return apiRequest<AdminUserListResponse>(`/api/admin/users?${search.toString()}`)
}

export function createCoach(payload: {
  username: string
  firstName: string
  lastName: string
  password: string
  passwordConfirm: string
}): Promise<User> {
  return apiRequest<User>('/api/admin/coaches', { method: 'POST', body: payload })
}

export function elevateUser(userId: string): Promise<User> {
  return apiRequest<User>(`/api/admin/users/${userId}/role`, {
    method: 'PATCH',
    body: { role: 'coach' },
  })
}

export function deleteUser(
  userId: string,
  payload: { adminPassword: string; confirmUsername: string },
): Promise<void> {
  return apiRequest<void>(`/api/admin/users/${userId}`, {
    method: 'DELETE',
    body: payload,
  })
}
