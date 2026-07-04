import { useQueryClient } from '@tanstack/react-query'
import { Card } from '../../components/ui/Card'
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
      <h1 className="text-2xl font-bold text-text">User Management</h1>

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-text">Create coach account</h2>
        <CreateCoachForm onSuccess={invalidate} />
      </Card>

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-text">Elevate client to coach</h2>
        <ElevateClientForm onSuccess={invalidate} />
      </Card>

      <DeleteAccountPanel onSuccess={invalidate} />
    </div>
  )
}
