import { NavLink } from 'react-router'
import { cn } from '@/lib/utils'

const ABAS = [
  { para: '/', rotulo: 'Projetos' },
  { para: '/hoje', rotulo: 'Tarefas de hoje' },
]

export function AbasPrincipais() {
  return (
    <nav aria-label="Principal" className="flex h-full gap-1">
      {ABAS.map(({ para, rotulo }) => (
        <NavLink
          key={para}
          to={para}
          end
          className={({ isActive }) =>
            cn(
              'flex items-center border-b-2 px-3 text-sm font-medium transition-colors',
              isActive
                ? 'border-foreground text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            )
          }
        >
          {rotulo}
        </NavLink>
      ))}
    </nav>
  )
}
