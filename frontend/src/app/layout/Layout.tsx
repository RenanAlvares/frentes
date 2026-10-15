import { Outlet } from 'react-router'
import { Cabecalho } from '@/app/layout/Cabecalho'

export function Layout() {
  return (
    <div className="min-h-svh bg-neutral-50">
      <Cabecalho />
      <main className="mx-auto max-w-screen-2xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
