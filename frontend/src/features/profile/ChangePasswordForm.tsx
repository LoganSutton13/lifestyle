import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { useToast } from '../../components/ui/Toast'
import { getErrorMessage } from '../../lib/errors'

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z.string().min(6, 'Password must be at least 6 characters'),
    newPasswordConfirm: z.string().min(10, 'Confirm your password'),
  })
  .refine((data) => data.newPassword === data.newPasswordConfirm, {
    message: 'Passwords do not match',
    path: ['newPasswordConfirm'],
  })

type PasswordForm = z.infer<typeof passwordSchema>

export interface ChangePasswordFormProps {
  onSubmit: (values: PasswordForm) => Promise<void>
}

export function ChangePasswordForm({ onSubmit }: ChangePasswordFormProps) {
  const { showToast } = useToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  })

  const submit = handleSubmit(async (values) => {
    try {
      await onSubmit(values)
      reset()
      showToast('Password updated')
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  })

  return (
    <form className="space-y-4" onSubmit={submit}>
      <Input
        label="Current password"
        type="password"
        autoComplete="current-password"
        error={errors.currentPassword?.message}
        {...register('currentPassword')}
      />
      <Input
        label="New password"
        type="password"
        autoComplete="new-password"
        error={errors.newPassword?.message}
        {...register('newPassword')}
      />
      <Input
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        error={errors.newPasswordConfirm?.message}
        {...register('newPasswordConfirm')}
      />
      <Button type="submit" loading={isSubmitting}>
        Change password
      </Button>
    </form>
  )
}
