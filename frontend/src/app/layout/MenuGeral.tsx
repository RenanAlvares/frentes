import { Ellipsis } from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

// 01-produto §3. "Exportar backup" entra com o backup (fase 5.3).
const ITENS = [
  { para: '/arquivados', rotulo: 'Arquivados' },
  { para: '/lixeira', rotulo: 'Lixeira' },
  { para: '/configuracoes', rotulo: 'Configurações' },
]

export function MenuGeral() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Menu">
          <Ellipsis />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {ITENS.map(({ para, rotulo }) => (
          <DropdownMenuItem key={para} asChild>
            <Link to={para}>{rotulo}</Link>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
