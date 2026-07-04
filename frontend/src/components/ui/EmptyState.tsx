import type { ReactNode } from 'react'
import { cn } from '../../lib/constants'

export interface EmptyStateProps {
  title: string
  description?: string
  icon?: ReactNode
  action?: ReactNode
  className?: string
}

export function EmptyState({ title, description, icon, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border bg-surface px-6 py-10 text-center',
        className,
      )}
    >
      {icon ? <div className="text-primary">{icon}</div> : null}
      <h3 className="text-lg font-semibold text-text">{title}</h3>
      {description ? <p className="max-w-sm text-sm text-textMuted">{description}</p> : null}
      {action}
    </div>
  )
}
