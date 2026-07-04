import { apiRequest } from '../../lib/apiClient'
import { DEFAULT_PAGE_SIZE } from '../../lib/constants'

export interface MealItem {
  id: string
  name: string
  category: string
  categoryLabel: string
  description: string
  assignedAt: string
}

export interface MealListResponse {
  items: MealItem[]
  page: number
  pageSize: number
  total: number
  hasNextPage: boolean
}

export interface MealQueryParams {
  page?: number
  pageSize?: number
  category?: string
}

export function fetchMeals(params: MealQueryParams = {}): Promise<MealListResponse> {
  const search = new URLSearchParams()
  search.set('page', String(params.page ?? 1))
  search.set('pageSize', String(params.pageSize ?? DEFAULT_PAGE_SIZE))
  if (params.category && params.category !== 'all') {
    search.set('category', params.category)
  }
  return apiRequest<MealListResponse>(`/api/me/meals?${search.toString()}`)
}
