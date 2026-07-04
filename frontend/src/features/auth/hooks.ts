import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  clearAuth,
  getCurrentUser,
  setAuth,
  setCurrentUser,
  subscribeAuth,
} from '../../lib/authStore'
import { getBrowserTimezone } from '../../lib/date'
import { getDefaultRedirect, type User, type UserRole } from '../../lib/constants'
import * as authApi from './api'

export const AUTH_QUERY_KEY = ['auth', 'me'] as const

export function useAuthUser(): User | null {
  const [user, setUser] = useState<User | null>(getCurrentUser())

  useEffect(() => subscribeAuth(setUser), [])

  return user
}

export function useAuthBootstrap() {
  const query = useQuery({
    queryKey: AUTH_QUERY_KEY,
    queryFn: async () => {
      try {
        return await authApi.fetchCurrentUser()
      } catch {
        clearAuth()
        return null
      }
    },
    retry: false,
    staleTime: Infinity,
  })

  useEffect(() => {
    if (query.data) {
      setCurrentUser(query.data)
    }
  }, [query.data])

  return query
}

export function useLogin(options?: { adminOnly?: boolean }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: authApi.LoginPayload) => {
      const data = await authApi.login(payload)
      if (options?.adminOnly && data.user.role !== 'admin') {
        clearAuth()
        await authApi.logout().catch(() => undefined)
        throw new Error('Admin access required.')
      }
      return data
    },
    onSuccess: (data) => {
      setAuth(data.user, data.accessToken)
      queryClient.setQueryData(AUTH_QUERY_KEY, data.user)

      if (data.user.role === 'admin' && !options?.adminOnly) {
        navigate('/admin')
        return
      }

      navigate(getDefaultRedirect(data.user.role))
    },
  })
}

export function useRegister() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      setAuth(data.user, data.accessToken)
      queryClient.setQueryData(AUTH_QUERY_KEY, data.user)
      navigate('/app/checklist')
    },
  })
}

export function useLogout() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthUser()

  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      clearAuth()
      queryClient.clear()
      const target = user?.role === 'admin' ? '/admin/login' : '/login'
      navigate(target)
    },
  })
}

export function useRegisterDefaults() {
  return {
    timezone: getBrowserTimezone(),
  }
}

export function hasRole(user: User | null, roles: UserRole[]): boolean {
  return !!user && roles.includes(user.role)
}
