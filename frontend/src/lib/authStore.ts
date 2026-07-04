import type { User } from './constants'

type AuthListener = (user: User | null) => void

let accessToken: string | null = null
let currentUser: User | null = null
const listeners = new Set<AuthListener>()

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getCurrentUser(): User | null {
  return currentUser
}

export function setCurrentUser(user: User | null): void {
  currentUser = user
  listeners.forEach((listener) => listener(user))
}

export function subscribeAuth(listener: AuthListener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function clearAuth(): void {
  accessToken = null
  currentUser = null
  listeners.forEach((listener) => listener(null))
}

export function setAuth(user: User, token: string): void {
  accessToken = token
  currentUser = user
  listeners.forEach((listener) => listener(user))
}
