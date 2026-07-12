import { cn } from '../../lib/cn'

export function portalNavLinkClassName(isActive: boolean): string {
  return cn(
    'flex min-h-touch items-center gap-2 rounded-xl px-4 text-sm font-medium transition-colors',
    isActive ? 'bg-primarySoft text-primaryDark' : 'text-textMuted hover:bg-surface hover:text-text',
  )
}

export const portalLogoutButtonClassName =
  'flex min-h-touch items-center gap-2 rounded-xl px-3 text-sm font-medium text-textMuted hover:bg-surface hover:text-text'
