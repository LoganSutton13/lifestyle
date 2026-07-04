import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/constants'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export function Card({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn('rounded-2xl border border-border bg-surfaceElevated p-4 shadow-sm', className)}
      {...props}
    >
      {children}
    </div>
  )
}
