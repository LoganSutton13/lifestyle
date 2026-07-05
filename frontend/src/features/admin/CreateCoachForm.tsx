import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { useToast } from '../../components/ui/Toast'
import { getErrorMessage } from '../../lib/errors'
import { createCoach } from './api'

const schema = z
  .object({
    username: z.string().min(3).max(30),
    firstName: z.string().min(1),
    lastName: z.string().min(1),
    password: z.string().min(6),
    passwordConfirm: z.string().min(6),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: 'Passwords do not match',
    path: ['passwordConfirm'],
  })

type FormValues = z.infer<typeof schema>

export function CreateCoachForm({ onSuccess }: { onSuccess?: () => void }) {
  const { showToast } = useToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const submit = handleSubmit(async (values) => {
    try {
      await createCoach(values)
      reset()
      showToast('Coach account created')
      onSuccess?.()
    } catch (error) {
      showToast(getErrorMessage(error), 'error')
    }
  })

  return (
    <form className="space-y-4" onSubmit={submit}>
      <Input label="Username" error={errors.username?.message} {...register('username')} />
      <Input label="First name" error={errors.firstName?.message} {...register('firstName')} />
      <Input label="Last name" error={errors.lastName?.message} {...register('lastName')} />
      <Input label="Password" type="password" error={errors.password?.message} {...register('password')} />
      <Input
        label="Confirm password"
        type="password"
        error={errors.passwordConfirm?.message}
        {...register('passwordConfirm')}
      />
      <Button type="submit" loading={isSubmitting}>
        Create coach
      </Button>
    </form>
  )
}
