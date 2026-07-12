import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { MutedText } from '../../components/ui/MutedText'
import { SectionTitle } from '../../components/ui/SectionTitle'
import { Spinner } from '../../components/ui/Spinner'
import { useToast } from '../../components/ui/Toast'
import { avatarUrl } from '../../lib/constants'
import { getErrorMessage } from '../../lib/errors'
import * as coachApi from './api'

export function ClientSearchAdd() {
  const [query, setQuery] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const searchQuery = useQuery({
    queryKey: ['coach-client-search', searchTerm],
    queryFn: () => coachApi.searchClients(searchTerm),
    enabled: searchTerm.length >= 2,
  })

  const addMutation = useMutation({
    mutationFn: coachApi.addClient,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach-clients'] })
      showToast('Client added')
      setSearchTerm('')
      setQuery('')
    },
    onError: (error) => {
      showToast(getErrorMessage(error), 'error')
    },
  })

  return (
    <Card className="space-y-4">
      <SectionTitle>Add existing client</SectionTitle>
      <div className="flex gap-2">
        <Input
          label="Search clients"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by username or name"
        />
        <Button
          type="button"
          className="mt-7 shrink-0"
          onClick={() => setSearchTerm(query.trim())}
        >
          <Search className="h-4 w-4" />
          Search
        </Button>
      </div>

      {searchQuery.isLoading ? <Spinner label="Searching..." /> : null}

      {searchQuery.isSuccess && searchTerm ? (
        <div className="space-y-2">
          {searchQuery.data.items.length === 0 ? (
            <MutedText>No clients found.</MutedText>
          ) : (
            searchQuery.data.items.map((client) => (
              <div
                key={client.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-border p-3"
              >
                <div className="flex items-center gap-3">
                  <img src={avatarUrl(client.avatarKey)} alt="" className="h-10 w-10" />
                  <div>
                    <p className="font-medium text-text">
                      {client.firstName} {client.lastName}
                    </p>
                    <p className="text-sm text-textMuted">@{client.username}</p>
                  </div>
                </div>
                <Button
                  type="button"
                  size="sm"
                  loading={addMutation.isPending}
                  onClick={() => addMutation.mutate(client.id)}
                >
                  <Plus className="h-4 w-4" />
                  Add
                </Button>
              </div>
            ))
          )}
        </div>
      ) : null}
    </Card>
  )
}
