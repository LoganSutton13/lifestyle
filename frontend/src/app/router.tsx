import { Navigate, Route, Routes } from 'react-router-dom'
import { AdminLayout } from '../components/layout/AdminLayout'
import { ClientAppLayout } from '../components/layout/ClientAppLayout'
import { CoachLayout } from '../components/layout/CoachLayout'
import { Spinner } from '../components/ui/Spinner'
import { AdminDashboard } from '../features/admin/AdminDashboard'
import { AdminSettingsPage } from '../features/admin/AdminSettingsPage'
import { AdminUsersPage } from '../features/admin/AdminUsersPage'
import { AdminLoginPage } from '../features/auth/AdminLoginPage'
import { AuthGuard, PublicOnlyGuard } from '../features/auth/AuthGuard'
import { LoginPage } from '../features/auth/LoginPage'
import { RegisterPage } from '../features/auth/RegisterPage'
import { useAuthBootstrap, useAuthUser } from '../features/auth/hooks'
import { ChecklistPage } from '../features/checklist/ChecklistPage'
import { CoachClientDetail } from '../features/coach/CoachClientDetail'
import { CoachDashboard } from '../features/coach/CoachDashboard'
import { DataPage } from '../features/measurements/DataPage'
import { MealPlanPage } from '../features/meals/MealPlanPage'
import { ProfilePage } from '../features/profile/ProfilePage'
import { getDefaultRedirect } from '../lib/constants'

function RootRedirect() {
  const user = useAuthUser()
  const { isLoading, data } = useAuthBootstrap()

  if (isLoading) {
    return <Spinner label="Loading..." />
  }

  if (!user || !data) {
    return <Navigate to="/login" replace />
  }

  return <Navigate to={getDefaultRedirect(user.role)} replace />
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />

      <Route element={<PublicOnlyGuard />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
      </Route>

      <Route element={<AuthGuard roles={['client']} />}>
        <Route element={<ClientAppLayout />}>
          <Route path="/app/meals" element={<MealPlanPage />} />
          <Route path="/app/checklist" element={<ChecklistPage />} />
          <Route path="/app/data" element={<DataPage />} />
          <Route path="/app/profile" element={<ProfilePage />} />
        </Route>
      </Route>

      <Route element={<AuthGuard roles={['coach']} />}>
        <Route element={<CoachLayout />}>
          <Route path="/coach" element={<CoachDashboard />} />
          <Route path="/coach/clients/:clientId" element={<CoachClientDetail />} />
          <Route path="/coach/profile" element={<ProfilePage />} />
        </Route>
      </Route>

      <Route element={<AuthGuard roles={['admin']} redirectTo="/admin/login" />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/settings" element={<AdminSettingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
