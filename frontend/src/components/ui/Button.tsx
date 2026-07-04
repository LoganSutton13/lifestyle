import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white hover:bg-primaryDark disabled:bg-primary/50',
  secondary: 'bg-primarySoft text-primaryDark hover:bg-primary/20',
  danger: 'bg-danger text-white hover:bg-danger/90',
  ghost: 'bg-transparent text-text hover:bg-surface',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'min-h-touch px-3 py-2 text-sm',
  md: 'min-h-touch px-4 py-2.5 text-base',
  lg: 'min-h-touch px-5 py-3 text-base',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-colors disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  ),
)

Button.displayName = 'Button'
