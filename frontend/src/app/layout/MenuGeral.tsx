import { Ellipsis } from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { URL_BACKUP } from '@/features/configuracoes/backup'

// 01-produto §3.
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
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          {/* RN-110: a API manda o zip como anexo; o navegador baixa. */}
          <a href={URL_BACKUP} download="">
            Exportar backup
          </a>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
