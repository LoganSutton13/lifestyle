import { useQueryClient } from '@tanstack/react-query'
import { Card } from '../../components/ui/Card'
import { PageTitle } from '../../components/ui/PageTitle'
import { SectionTitle } from '../../components/ui/SectionTitle'
import { CreateCoachForm } from './CreateCoachForm'
import { DeleteAccountPanel } from './DeleteAccountPanel'
import { ElevateClientForm } from './ElevateClientForm'

export function AdminUsersPage() {
  const queryClient = useQueryClient()

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    void queryClient.invalidateQueries({ queryKey: ['admin-users-clients'] })
    void queryClient.invalidateQueries({ queryKey: ['admin-users-all'] })
  }

  return (
    <div className="space-y-6">
      <PageTitle>User Management</PageTitle>

      <Card>
        <SectionTitle className="mb-4">Create coach account</SectionTitle>
        <CreateCoachForm onSuccess={invalidate} />
      </Card>

      <Card>
        <SectionTitle className="mb-4">Elevate client to coach</SectionTitle>
        <ElevateClientForm onSuccess={invalidate} />
      </Card>

      <DeleteAccountPanel onSuccess={invalidate} />
    </div>
  )
}
