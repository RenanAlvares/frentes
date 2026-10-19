import { NavLink } from 'react-router'
import { useTarefasHoje } from '@/features/tarefas/hooks/useTarefas'
import { cn } from '@/lib/utils'

const ABAS = [
  { para: '/', rotulo: 'Projetos' },
  { para: '/hoje', rotulo: 'Tarefas de hoje' },
]

export function AbasPrincipais() {
  const { data } = useTarefasHoje()
  // RN-63: atrasadas + hoje; oculto quando 0 (01 §3).
  const pendentes = data ? data.atrasadas.length + data.hoje.length : 0

  return (
    <nav aria-label="Principal" className="flex h-full gap-1">
      {ABAS.map(({ para, rotulo }) => (
        <NavLink
          key={para}
          to={para}
          end
          className={({ isActive }) =>
            cn(
              'flex items-center gap-1.5 border-b-2 px-3 text-sm font-medium transition-colors',
              isActive
                ? 'border-foreground text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            )
          }
        >
          {rotulo}
          {para === '/hoje' && pendentes > 0 && (
            <span className="rounded-full bg-red-600 px-1.5 text-xs leading-5 font-semibold text-white">
              {pendentes}
            </span>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
