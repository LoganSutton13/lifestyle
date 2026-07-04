import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Users } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { Spinner } from '../../components/ui/Spinner'
import { avatarUrl } from '../../lib/constants'
import { getErrorMessage } from '../../lib/errors'
import { fetchCoachClients } from './api'
import { ClientSearchAdd } from './ClientSearchAdd'

export function CoachDashboard() {
  const query = useQuery({
    queryKey: ['coach-clients'],
    queryFn: () => fetchCoachClients({ page: 1 }),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Clients</h1>

      <ClientSearchAdd />

      {query.isLoading ? <Spinner label="Loading clients..." /> : null}

      {query.isError ? (
        <p className="rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          {getErrorMessage(query.error)}
        </p>
      ) : null}

      {query.isSuccess && query.data.items.length === 0 ? (
        <EmptyState
          title="No clients yet"
          description="Search for existing client accounts and add them to your list."
          icon={<Users className="h-8 w-8" />}
        />
      ) : null}

      {query.isSuccess && query.data.items.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {query.data.items.map((client) => (
            <Link key={client.id} to={`/coach/clients/${client.id}`}>
              <Card className="transition-shadow hover:shadow-md">
                <div className="flex items-start gap-3">
                  <img src={avatarUrl(client.avatarKey)} alt="" className="h-12 w-12 rounded-xl bg-surface p-1" />
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-text">
                      {client.firstName} {client.lastName}
                    </p>
                    <p className="text-sm text-textMuted">@{client.username}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-textMuted">
                      {client.latestBodyWeight != null ? (
                        <span>Weight: {client.latestBodyWeight} lbs</span>
                      ) : null}
                      <span>
                        Today: {client.todayCompletedTasks}/{client.todayTotalTasks} tasks
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  )
}
