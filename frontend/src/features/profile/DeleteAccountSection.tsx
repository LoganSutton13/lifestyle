import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { useToast } from '../../components/ui/Toast'
import { getErrorMessage } from '../../lib/errors'

const deleteSchema = z.object({
  password: z.string().min(1, 'Password is required'),
})

type DeleteForm = z.infer<typeof deleteSchema>

export interface DeleteAccountSectionProps {
  onDelete: (password: string) => Promise<void>
}

export function DeleteAccountSection({ onDelete }: DeleteAccountSectionProps) {
  const { showToast } = useToast()
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DeleteForm>({
    resolver: zodResolver(deleteSchema),
  })

  const submit = handleSubmit(async (values) => {
    const confirmed = window.confirm(
      'This will permanently delete your account and associated data. Continue?',
    )
    if (!confirmed) {
      return
    }

    try {
      await onDelete(values.password)
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  })

  return (
    <section className="space-y-4 rounded-2xl border border-danger/30 bg-danger/5 p-4">
      <div>
        <h2 className="text-lg font-semibold text-danger">Delete account</h2>
        <p className="mt-1 text-sm text-textMuted">
          This will permanently delete your account and associated application data.
        </p>
      </div>
      <form className="space-y-4" onSubmit={submit}>
        <Input
          label="Current password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" variant="danger" loading={isSubmitting}>
          Delete my account
        </Button>
      </form>
    </section>
  )
}
