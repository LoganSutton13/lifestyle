import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

type MutedTextSize = 'sm' | 'xs'
type MutedTextAs = 'p' | 'span'

export interface MutedTextProps extends HTMLAttributes<HTMLElement> {
  as?: MutedTextAs
  size?: MutedTextSize
  children: ReactNode
}

const sizeClasses: Record<MutedTextSize, string> = {
  sm: 'text-sm text-textMuted',
  xs: 'text-xs text-textMuted',
}

export function MutedText({
  as: Component = 'p',
  size = 'sm',
  className,
  children,
  ...props
}: MutedTextProps) {
  return (
    <Component className={cn(sizeClasses[size], className)} {...props}>
      {children}
    </Component>
  )
}
