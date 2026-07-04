import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { useToast } from '../../components/ui/Toast'
import { avatarUrl } from '../../lib/constants'
import { getBrowserTimezone } from '../../lib/date'
import { getErrorMessage } from '../../lib/errors'
import { changePassword, deleteAccount, updateProfile } from '../auth/api'
import { AUTH_QUERY_KEY, useAuthUser, useLogout } from '../auth/hooks'
import { AvatarPicker } from './AvatarPicker'
import { ChangePasswordForm } from './ChangePasswordForm'
import { DeleteAccountSection } from './DeleteAccountSection'

interface ProfileForm {
  username: string
  firstName: string
  lastName: string
  timezone: string
}

export function ProfilePage() {
  const user = useAuthUser()
  const logout = useLogout()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [avatarKey, setAvatarKey] = useState(user?.avatarKey ?? 'avocado')

  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting },
  } = useForm<ProfileForm>()

  useEffect(() => {
    if (user) {
      reset({
        username: user.username,
        firstName: user.firstName,
        lastName: user.lastName,
        timezone: user.timezone || getBrowserTimezone(),
      })
      setAvatarKey(user.avatarKey)
    }
  }, [user, reset])

  const profileMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(AUTH_QUERY_KEY, updatedUser)
      showToast('Profile updated')
    },
    onError: (error) => {
      showToast(getErrorMessage(error), 'error')
    },
  })

  if (!user) {
    return null
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Profile</h1>

      <Card className="flex items-center gap-4">
        <img src={avatarUrl(avatarKey)} alt="" className="h-16 w-16 rounded-2xl bg-surface p-2" />
        <div>
          <p className="text-lg font-semibold text-text">
            {user.firstName} {user.lastName}
          </p>
          <p className="text-sm text-textMuted">@{user.username}</p>
        </div>
      </Card>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-text">Avatar</h2>
        <AvatarPicker value={avatarKey} onChange={setAvatarKey} />
      </section>

      <Card>
        <form
          className="space-y-4"
          onSubmit={handleSubmit((values) =>
            profileMutation.mutate({ ...values, avatarKey }),
          )}
        >
          <h2 className="text-lg font-semibold text-text">Account information</h2>
          <Input label="Username" {...register('username')} />
          <Input label="First name" {...register('firstName')} />
          <Input label="Last name" {...register('lastName')} />
          <Input label="Timezone" {...register('timezone')} />
          <Button type="submit" loading={isSubmitting || profileMutation.isPending}>
            Save profile
          </Button>
        </form>
      </Card>

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-text">Change password</h2>
        <ChangePasswordForm onSubmit={(values) => changePassword(values)} />
      </Card>

      <DeleteAccountSection
        onDelete={async (password) => {
          await deleteAccount(password)
          logout.mutate()
        }}
      />
    </div>
  )
}
