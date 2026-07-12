import type { ElementType, HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

type PageTitleSize = 'md' | 'lg'

export interface PageTitleProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType
  size?: PageTitleSize
  children: ReactNode
}

const sizeClasses: Record<PageTitleSize, string> = {
  md: 'text-2xl font-bold text-text',
  lg: 'text-3xl font-bold text-text',
}

export function PageTitle({
  as: Component = 'h1',
  size = 'md',
  className,
  children,
  ...props
}: PageTitleProps) {
  return (
    <Component className={cn(sizeClasses[size], className)} {...props}>
      {children}
    </Component>
  )
}
