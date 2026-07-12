import { NavLink, Outlet } from 'react-router-dom'
import { Dumbbell, LayoutDashboard, LogOut, Settings, Users } from 'lucide-react'
import { SectionTitle } from '../ui/SectionTitle'
import { useLogout } from '../../features/auth/hooks'
import { portalLogoutButtonClassName, portalNavLinkClassName } from './portalNav'

const navItems = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/users', label: 'Users', icon: Users, end: false },
  { to: '/admin/exercises', label: 'Exercises', icon: Dumbbell, end: false },
  { to: '/admin/settings', label: 'Settings', icon: Settings, end: false },
] as const

export function AdminLayout() {
  const logout = useLogout()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-background">
        <div className="mx-auto flex max-w-dashboard items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-2">
            <LayoutDashboard className="h-6 w-6 text-primary" />
            <SectionTitle as="span">Admin Portal</SectionTitle>
          </div>
          <button
            type="button"
            onClick={() => logout.mutate()}
            className={portalLogoutButtonClassName}
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
        <nav className="mx-auto flex max-w-dashboard flex-wrap gap-2 px-4 pb-3">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => portalNavLinkClassName(isActive)}
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
