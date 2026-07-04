import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Spinner } from '../../components/ui/Spinner'
import { getDefaultRedirect } from '../../lib/constants'
import { useAuthBootstrap, useAuthUser, hasRole } from './hooks'
import type { UserRole } from '../../lib/constants'

interface AuthGuardProps {
  roles?: UserRole[]
  redirectTo?: string
}

export function AuthGuard({ roles, redirectTo }: AuthGuardProps) {
  const location = useLocation()
  const user = useAuthUser()
  const { isLoading, isError, data } = useAuthBootstrap()

  if (isLoading) {
    return <Spinner label="Checking session..." />
  }

  const isAuthenticated = !!user && !isError && data !== null

  if (!isAuthenticated) {
    const fallback = redirectTo ?? (location.pathname.startsWith('/admin') ? '/admin/login' : '/login')
    return <Navigate to={fallback} replace state={{ from: location.pathname }} />
  }

  if (roles && !hasRole(user, roles)) {
    return <Navigate to={getDefaultRedirect(user.role)} replace />
  }

  return <Outlet />
}

export function PublicOnlyGuard() {
  const user = useAuthUser()
  const { isLoading } = useAuthBootstrap()

  if (isLoading) {
    return <Spinner label="Loading..." />
  }

  if (!user) {
    return <Outlet />
  }

  return <Navigate to={getDefaultRedirect(user.role)} replace />
}
