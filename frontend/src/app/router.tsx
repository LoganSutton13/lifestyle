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
import { AdminExercisesPage } from '../features/admin/AdminExercisesPage'
import { CoachClientDetail } from '../features/coach/CoachClientDetail'
import { CoachDashboard } from '../features/coach/CoachDashboard'
import { CoachExercisesPage } from '../features/coach/workouts/CoachExercisesPage'
import { WorkoutTemplateEditor } from '../features/coach/workouts/WorkoutTemplateEditor'
import { WorkoutTemplatesPage } from '../features/coach/workouts/WorkoutTemplatesPage'
import { DataPage } from '../features/measurements/DataPage'
import { MealPlanPage } from '../features/meals/MealPlanPage'
import { ProfilePage } from '../features/profile/ProfilePage'
import { ActiveWorkoutPage } from '../features/workouts/ActiveWorkoutPage'
import { WorkoutHistoryDetailPage } from '../features/workouts/WorkoutHistoryDetailPage'
import { WorkoutsPage } from '../features/workouts/WorkoutsPage'
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
          <Route path="/app/workouts" element={<WorkoutsPage />} />
          <Route path="/app/workouts/active/:sessionId" element={<ActiveWorkoutPage />} />
          <Route path="/app/workouts/history/:sessionId" element={<WorkoutHistoryDetailPage />} />
          <Route path="/app/data" element={<DataPage />} />
          <Route path="/app/profile" element={<ProfilePage />} />
        </Route>
      </Route>

      <Route element={<AuthGuard roles={['coach']} />}>
        <Route element={<CoachLayout />}>
          <Route path="/coach" element={<CoachDashboard />} />
          <Route path="/coach/clients/:clientId" element={<CoachClientDetail />} />
          <Route path="/coach/exercises" element={<CoachExercisesPage />} />
          <Route path="/coach/workouts/templates" element={<WorkoutTemplatesPage />} />
          <Route path="/coach/workouts/templates/:templateId" element={<WorkoutTemplateEditor />} />
          <Route path="/coach/profile" element={<ProfilePage />} />
        </Route>
      </Route>

      <Route element={<AuthGuard roles={['admin']} redirectTo="/admin/login" />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/exercises" element={<AdminExercisesPage />} />
          <Route path="/admin/settings" element={<AdminSettingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
