import { cn } from '../../lib/constants'

export interface SpinnerProps {
  className?: string
  label?: string
}

export function Spinner({ className, label = 'Loading' }: SpinnerProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 py-8', className)} role="status">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primarySoft border-t-primary" />
      <span className="text-sm text-textMuted">{label}</span>
    </div>
  )
}
