import { Outlet } from 'react-router-dom'
import { BottomNav } from './BottomNav'

export function ClientAppLayout() {
  return (
    <div className="mx-auto min-h-screen max-w-client bg-background pb-nav">
      <main className="px-4 py-5">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  )
}
