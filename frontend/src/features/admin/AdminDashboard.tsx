import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card } from '../../components/ui/Card'
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
    return (
      <p className="rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
        {getErrorMessage(query.error)}
      </p>
    )
  }

  const stats = query.data!

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Admin Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-textMuted">Clients</p>
          <p className="text-3xl font-bold text-text">{stats.clients}</p>
        </Card>
        <Card>
          <p className="text-sm text-textMuted">Coaches</p>
          <p className="text-3xl font-bold text-text">{stats.coaches}</p>
        </Card>
        <Card>
          <p className="text-sm text-textMuted">Admins</p>
          <p className="text-3xl font-bold text-text">{stats.admins}</p>
        </Card>
      </div>

      <Card className="space-y-3">
        <h2 className="text-lg font-semibold text-text">Quick links</h2>
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
        <h2 className="text-lg font-semibold text-text">Recent users</h2>
        {stats.recentUsers.length === 0 ? (
          <p className="text-sm text-textMuted">No recent users.</p>
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
