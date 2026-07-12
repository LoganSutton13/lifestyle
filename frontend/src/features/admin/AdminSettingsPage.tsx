import { Card } from '../../components/ui/Card'
import { PageTitle } from '../../components/ui/PageTitle'
import { SectionTitle } from '../../components/ui/SectionTitle'
import { changePassword } from '../auth/api'
import { ChangePasswordForm } from '../profile/ChangePasswordForm'

export function AdminSettingsPage() {
  return (
    <div className="space-y-6">
      <PageTitle>Admin Settings</PageTitle>
      <Card>
        <SectionTitle className="mb-4">Change password</SectionTitle>
        <ChangePasswordForm onSubmit={(values) => changePassword(values)} />
      </Card>
    </div>
  )
}
