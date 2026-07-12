import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Alert } from '../../components/ui/Alert'
import { Card } from '../../components/ui/Card'
import { MutedText } from '../../components/ui/MutedText'
import { PageTitle } from '../../components/ui/PageTitle'
import { SectionTitle } from '../../components/ui/SectionTitle'
import { Spinner } from '../../components/ui/Spinner'
import { getErrorMessage } from '../../lib/errors'
import { fetchAdminStats } from './api'

export function AdminDashboard() {
  const query = useQuery({
    queryKey: ['admin-stats'],
    queryFn: fetchAdminStats,
  })

  if (query.isLoading) {
    return <Spinner label="Loading dashboard..." />
  }

  if (query.isError) {
    return <Alert>{getErrorMessage(query.error)}</Alert>
  }

  const stats = query.data!

  return (
    <div className="space-y-6">
      <PageTitle>Admin Dashboard</PageTitle>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <MutedText>Clients</MutedText>
          <p className="text-3xl font-bold text-text">{stats.clients}</p>
        </Card>
        <Card>
          <MutedText>Coaches</MutedText>
          <p className="text-3xl font-bold text-text">{stats.coaches}</p>
        </Card>
        <Card>
          <MutedText>Admins</MutedText>
          <p className="text-3xl font-bold text-text">{stats.admins}</p>
        </Card>
      </div>

      <Card className="space-y-3">
        <SectionTitle>Quick links</SectionTitle>
        <div className="flex flex-wrap gap-2">
          <Link to="/admin/users" className="rounded-xl bg-primarySoft px-4 py-2 text-sm font-medium text-primaryDark">
            Manage users
          </Link>
          <Link to="/admin/settings" className="rounded-xl bg-primarySoft px-4 py-2 text-sm font-medium text-primaryDark">
            Admin settings
          </Link>
        </div>
      </Card>

      <Card className="space-y-3">
        <SectionTitle>Recent users</SectionTitle>
        {stats.recentUsers.length === 0 ? (
          <MutedText>No recent users.</MutedText>
        ) : (
          <ul className="space-y-2">
            {stats.recentUsers.map((user) => (
              <li key={user.id} className="flex items-center justify-between text-sm">
                <span className="text-text">
                  {user.firstName} {user.lastName} (@{user.username})
                </span>
                <span className="capitalize text-textMuted">{user.role}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
