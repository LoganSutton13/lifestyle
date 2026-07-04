import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Shield } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { getErrorMessage } from '../../lib/errors'
import { useLogin } from './hooks'

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

type LoginForm = z.infer<typeof loginSchema>

export function AdminLoginPage() {
  const login = useLogin({ adminOnly: true })
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const errorMessage =
    login.isError && login.error instanceof Error && login.error.message === 'Admin access required.'
      ? 'Admin access required.'
      : login.isError
        ? getErrorMessage(login.error)
        : null

  return (
    <div className="mx-auto flex min-h-screen max-w-client flex-col justify-center px-4 py-8">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primarySoft text-primary">
          <Shield className="h-7 w-7" />
        </div>
        <h1 className="text-3xl font-bold text-text">Admin Sign In</h1>
        <p className="mt-2 text-textMuted">Restricted access for administrators only</p>
      </div>

      <Card>
        <form
          className="flex flex-col gap-4"
          onSubmit={handleSubmit((values) => login.mutate(values))}
        >
          <Input label="Username" autoComplete="username" error={errors.username?.message} {...register('username')} />
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register('password')}
          />

          {errorMessage ? <p className="text-sm text-danger">{errorMessage}</p> : null}

          <Button type="submit" loading={login.isPending} className="w-full">
            Sign in as admin
          </Button>
        </form>
      </Card>
    </div>
  )
}
