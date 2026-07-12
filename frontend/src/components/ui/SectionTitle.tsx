import type { ElementType, HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

export interface SectionTitleProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType
  children: ReactNode
}

export function SectionTitle({
  as: Component = 'h2',
  className,
  children,
  ...props
}: SectionTitleProps) {
  return (
    <Component className={cn('text-lg font-semibold text-text', className)} {...props}>
      {children}
    </Component>
  )
}
