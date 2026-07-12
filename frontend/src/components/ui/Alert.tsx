import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

type AlertVariant = 'error' | 'success'

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant
  children: ReactNode
}

const variantClasses: Record<AlertVariant, string> = {
  error: 'rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger',
  success: 'rounded-xl bg-success/10 px-4 py-3 text-sm text-success',
}

export function Alert({ variant = 'error', className, children, ...props }: AlertProps) {
  return (
    <div role="alert" className={cn(variantClasses[variant], className)} {...props}>
      {children}
    </div>
  )
}
