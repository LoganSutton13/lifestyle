import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { Button } from '../../components/ui/Button'
import { DangerZone } from '../../components/ui/DangerZone'
import { Input } from '../../components/ui/Input'
import { MutedText } from '../../components/ui/MutedText'
import { Select } from '../../components/ui/Select'
import { useToast } from '../../components/ui/Toast'
import { getErrorMessage } from '../../lib/errors'
import { deleteUser, fetchAdminUsers } from './api'

const schema = z.object({
  userId: z.string().min(1, 'Select a user'),
  adminPassword: z.string().min(1, 'Admin password is required'),
  confirmUsername: z.string().min(1, 'Confirm username is required'),
})

type FormValues = z.infer<typeof schema>

export function DeleteAccountPanel({ onSuccess }: { onSuccess?: () => void }) {
  const { showToast } = useToast()
  const [search, setSearch] = useState('')

  const usersQuery = useQuery({
    queryKey: ['admin-users-all', search],
    queryFn: () => fetchAdminUsers({ search, page: 1 }),
  })

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const selectedUser = usersQuery.data?.items.find((user) => user.id === watch('userId'))

  const submit = handleSubmit(async (values) => {
    const confirmed = window.confirm('This will permanently delete the selected account. Continue?')
    if (!confirmed) return

    try {
      await deleteUser(values.userId, {
        adminPassword: values.adminPassword,
        confirmUsername: values.confirmUsername,
      })
      showToast('Account deleted')
      onSuccess?.()
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  })

  const userOptions =
    usersQuery.data?.items.map((user) => ({
      value: user.id,
      label: `${user.firstName} ${user.lastName} (@${user.username}) - ${user.role}`,
    })) ?? []

  return (
    <DangerZone as="form" title="Delete any account" onSubmit={submit}>
      <MutedText>
        Requires your admin password and exact username confirmation.
      </MutedText>
      <Input label="Search users" value={search} onChange={(e) => setSearch(e.target.value)} />
      <Select
        label="User to delete"
        options={[{ value: '', label: 'Select a user' }, ...userOptions]}
        error={errors.userId?.message}
        {...register('userId')}
      />
      <Input
        label="Type target username exactly"
        placeholder={selectedUser?.username ?? 'username'}
        error={errors.confirmUsername?.message}
        {...register('confirmUsername')}
      />
      <Input
        label="Your admin password"
        type="password"
        error={errors.adminPassword?.message}
        {...register('adminPassword')}
      />
      <Button type="submit" variant="danger" loading={isSubmitting}>
        Delete account
      </Button>
    </DangerZone>
  )
}
