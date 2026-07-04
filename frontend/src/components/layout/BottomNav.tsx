import { NavLink } from 'react-router-dom'
import { CheckSquare, LineChart, UserCircle, Utensils } from 'lucide-react'
import { cn } from '../../lib/constants'

const tabs = [
  { to: '/app/meals', label: 'Meal Plan', icon: Utensils },
  { to: '/app/checklist', label: 'Checklist', icon: CheckSquare },
  { to: '/app/data', label: 'Data', icon: LineChart },
  { to: '/app/profile', label: 'Profile', icon: UserCircle },
] as const

export function BottomNav() {
  return (
    <nav
      aria-label="Main navigation"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background shadow-[0_-2px_10px_rgba(0,0,0,0.04)] safe-bottom"
    >
      <div className="mx-auto flex max-w-client items-stretch justify-around px-2">
        {tabs.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex min-h-touch flex-1 flex-col items-center justify-center gap-1 px-1 py-2 text-xs font-medium transition-colors',
                isActive ? 'text-primary' : 'text-textMuted hover:text-text',
              )
            }
          >
            <Icon className="h-5 w-5" aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
