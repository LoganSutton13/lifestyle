import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link } from 'react-router-dom'
import { z } from 'zod'
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

export function LoginPage() {
  const login = useLogin()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  return (
    <div className="mx-auto flex min-h-screen max-w-client flex-col justify-center px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-text">Elevate Fitness</h1>
        <p className="mt-2 text-textMuted">Sign in to your account</p>
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

          {login.isError ? (
            <p className="text-sm text-danger">{getErrorMessage(login.error)}</p>
          ) : null}

          <Button type="submit" loading={login.isPending} className="w-full">
            Sign in
          </Button>
        </form>
      </Card>

      <p className="mt-6 text-center text-sm text-textMuted">
        New here?{' '}
        <Link to="/register" className="font-medium text-primary hover:text-primaryDark">
          Create an account
        </Link>
      </p>
    </div>
  )
}
