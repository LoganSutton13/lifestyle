import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, LogOut, UserCircle, Users } from 'lucide-react'
import { cn } from '../../lib/constants'
import { useLogout } from '../../features/auth/hooks'

const navItems = [
  { to: '/coach', label: 'Clients', icon: Users, end: true },
  { to: '/coach/profile', label: 'Profile', icon: UserCircle, end: false },
] as const

export function CoachLayout() {
  const logout = useLogout()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-background">
        <div className="mx-auto flex max-w-dashboard items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-2 text-primary">
            <LayoutDashboard className="h-6 w-6" />
            <span className="text-lg font-semibold text-text">Coach Portal</span>
          </div>
          <button
            type="button"
            onClick={() => logout.mutate()}
            className="flex min-h-touch items-center gap-2 rounded-xl px-3 text-sm font-medium text-textMuted hover:bg-surface hover:text-text"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
        <nav className="mx-auto flex max-w-dashboard gap-2 px-4 pb-3">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex min-h-touch items-center gap-2 rounded-xl px-4 text-sm font-medium transition-colors',
                  isActive ? 'bg-primarySoft text-primaryDark' : 'text-textMuted hover:bg-surface hover:text-text',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-dashboard px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
