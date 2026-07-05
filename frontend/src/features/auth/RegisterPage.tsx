import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link } from 'react-router-dom'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { getErrorMessage } from '../../lib/errors'
import { useRegister, useRegisterDefaults } from './hooks'

const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(30, 'Username must be at most 30 characters')
      .regex(/^[a-zA-Z0-9_.-]+$/, 'Username contains invalid characters'),
    firstName: z.string().min(1, 'First name is required'),
    lastName: z.string().min(1, 'Last name is required'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
    passwordConfirm: z.string().min(6, 'Confirm your password'),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: 'Passwords do not match',
    path: ['passwordConfirm'],
  })

type RegisterForm = z.infer<typeof registerSchema>

export function RegisterPage() {
  const registerMutation = useRegister()
  const defaults = useRegisterDefaults()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  })

  return (
    <div className="mx-auto flex min-h-screen max-w-client flex-col justify-center px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-text">Create account</h1>
        <p className="mt-2 text-textMuted">Join as a client to track your fitness journey</p>
      </div>

      <Card>
        <form
          className="flex flex-col gap-4"
          onSubmit={handleSubmit((values) =>
            registerMutation.mutate({
              ...values,
              timezone: defaults.timezone,
            }),
          )}
        >
          <Input label="Username" autoComplete="username" error={errors.username?.message} {...register('username')} />
          <Input label="First name" autoComplete="given-name" error={errors.firstName?.message} {...register('firstName')} />
          <Input label="Last name" autoComplete="family-name" error={errors.lastName?.message} {...register('lastName')} />
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password')}
          />
          <Input
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            error={errors.passwordConfirm?.message}
            {...register('passwordConfirm')}
          />

          {registerMutation.isError ? (
            <p className="text-sm text-danger">{getErrorMessage(registerMutation.error)}</p>
          ) : null}

          <Button type="submit" loading={registerMutation.isPending} className="w-full">
            Register
          </Button>
        </form>
      </Card>

      <p className="mt-6 text-center text-sm text-textMuted">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-primary hover:text-primaryDark">
          Sign in
        </Link>
      </p>
    </div>
  )
}
