import { Card } from '../../components/ui/Card'
import { changePassword } from '../auth/api'
import { ChangePasswordForm } from '../profile/ChangePasswordForm'

export function AdminSettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Admin Settings</h1>
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-text">Change password</h2>
        <ChangePasswordForm onSubmit={(values) => changePassword(values)} />
      </Card>
    </div>
  )
}
