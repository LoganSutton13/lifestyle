import { apiRequest } from '../../lib/apiClient'
import type { User } from '../../lib/constants'

export interface AuthResponse {
  user: User
  accessToken: string
}

export interface RegisterPayload {
  username: string
  firstName: string
  lastName: string
  password: string
  passwordConfirm: string
  timezone?: string
}

export interface LoginPayload {
  username: string
  password: string
}

export function register(payload: RegisterPayload): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: payload,
    skipAuth: true,
  })
}

export function login(payload: LoginPayload): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: payload,
    skipAuth: true,
  })
}

export function logout(): Promise<void> {
  return apiRequest<void>('/api/auth/logout', { method: 'POST' })
}

export function fetchCurrentUser(): Promise<User> {
  return apiRequest<User>('/api/auth/me')
}

export function updateProfile(data: Partial<User>): Promise<User> {
  return apiRequest<User>('/api/me', { method: 'PUT', body: data })
}

export function changePassword(data: {
  currentPassword: string
  newPassword: string
  newPasswordConfirm: string
}): Promise<void> {
  return apiRequest<void>('/api/me/change-password', { method: 'POST', body: data })
}

export function deleteAccount(password: string): Promise<void> {
  return apiRequest<void>('/api/me', { method: 'DELETE', body: { password } })
}
