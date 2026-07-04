import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { useToast } from '../../components/ui/Toast'
import { getErrorMessage } from '../../lib/errors'
import { elevateUser, fetchAdminUsers } from './api'

const schema = z.object({
  userId: z.string().min(1, 'Select a client'),
})

type FormValues = z.infer<typeof schema>

export function ElevateClientForm({ onSuccess }: { onSuccess?: () => void }) {
  const { showToast } = useToast()
  const [search, setSearch] = useState('')

  const usersQuery = useQuery({
    queryKey: ['admin-users-clients', search],
    queryFn: () => fetchAdminUsers({ role: 'client', search, page: 1 }),
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const userOptions =
    usersQuery.data?.items.map((user) => ({
      value: user.id,
      label: `${user.firstName} ${user.lastName} (@${user.username})`,
    })) ?? []

  const submit = handleSubmit(async (values) => {
    try {
      await elevateUser(values.userId)
      reset()
      showToast('Client elevated to coach')
      onSuccess?.()
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  })

  return (
    <form className="space-y-4" onSubmit={submit}>
      <Input label="Search clients" value={search} onChange={(e) => setSearch(e.target.value)} />
      <Select
        label="Client to elevate"
        options={[{ value: '', label: 'Select a client' }, ...userOptions]}
        error={errors.userId?.message}
        {...register('userId')}
      />
      <Button type="submit" loading={isSubmitting}>
        Elevate to coach
      </Button>
    </form>
  )
}
