import {
  clearAuth,
  getAccessToken,
  setAccessToken,
} from './authStore'
import { parseApiError } from './errors'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

let refreshPromise: Promise<string | null> | null = null

function isAdminRoute(): boolean {
  return window.location.pathname.startsWith('/admin')
}

function isPublicPath(): boolean {
  const path = window.location.pathname
  return path === '/login' || path === '/register' || path === '/admin/login' || path === '/'
}

function redirectToLogin(): void {
  if (isPublicPath()) {
    return
  }
  const target = isAdminRoute() ? '/admin/login' : '/login'
  if (!window.location.pathname.startsWith(target)) {
    window.location.assign(target)
  }
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })

        if (!response.ok) {
          clearAuth()
          redirectToLogin()
          return null
        }

        const data = (await response.json()) as { accessToken: string }
        setAccessToken(data.accessToken)
        return data.accessToken
      } catch {
        clearAuth()
        redirectToLogin()
        return null
      } finally {
        refreshPromise = null
      }
    })()
  }

  return refreshPromise
}

export interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  skipAuth?: boolean
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { body, skipAuth = false, headers, ...rest } = options

  const requestHeaders = new Headers(headers)
  if (body !== undefined && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json')
  }

  if (!skipAuth) {
    const token = getAccessToken()
    if (token) {
      requestHeaders.set('Authorization', `Bearer ${token}`)
    }
  }

  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`

  const execute = async (retried: boolean): Promise<T> => {
    const response = await fetch(url, {
      ...rest,
      credentials: 'include',
      headers: requestHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })

    if (response.status === 401 && !skipAuth && !retried) {
      const newToken = await refreshAccessToken()
      if (newToken) {
        requestHeaders.set('Authorization', `Bearer ${newToken}`)
        return execute(true)
      }
      throw await parseApiError(response)
    }

    if (!response.ok) {
      throw await parseApiError(response)
    }

    if (response.status === 204) {
      return undefined as T
    }

    return (await response.json()) as T
  }

  return execute(false)
}

export { API_BASE_URL }
