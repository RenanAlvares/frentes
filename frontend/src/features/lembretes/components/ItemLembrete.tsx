import { CheckCheck, Ellipsis, Pencil, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { Lembrete } from '@/features/lembretes/formulario'
import {
  useDarBaixa,
  useDesfazerBaixa,
  useExcluirLembrete,
  useRestaurarLembrete,
} from '@/features/lembretes/hooks/useLembretes'
import { anoDe, formatarData, formatarDataCurta, textoRelativo } from '@/lib/datas'
import { avisarComDesfazer } from '@/lib/desfazer'
import { cn, FOCO_VISIVEL } from '@/lib/utils'

type Props = {
  lembrete: Lembrete
  /** "Hoje" da API, para mostrar dd/mm no ano atual. */
  hoje: string | undefined
  onEditar: () => void
}

/**
 * 01 §4.4: título, data, regra, texto relativo e menu (Editar, Dar baixa, Excluir).
 * Na janela de aviso (RN-42): borda âmbar. Vencido: texto vermelho.
 */
export function ItemLembrete({ lembrete, hoje, onEditar }: Props) {
  const baixa = useDarBaixa(lembrete.projeto_id)
  const desfazer = useDesfazerBaixa(lembrete.projeto_id)
  const excluir = useExcluirLembrete(lembrete.projeto_id)
  const restaurar = useRestaurarLembrete(lembrete.projeto_id)
  const vencido = lembrete.dias_restantes < 0
  const data = hoje
    ? formatarDataCurta(lembrete.vencimento, anoDe(hoje))
    : formatarData(lembrete.vencimento)
  const aoFalhar = { onError: (erro: unknown) => toast.error(mensagemDoErro(erro)) }

  function darBaixa() {
    baixa.mutate(lembrete.id, {
      ...aoFalhar,
      onSuccess: () =>
        avisarComDesfazer('Baixa registrada', () => desfazer.mutateAsync(lembrete.id)),
    })
  }

  function excluirLembrete() {
    excluir.mutate(lembrete.id, {
      ...aoFalhar,
      onSuccess: () =>
        avisarComDesfazer('Movido para a lixeira', () => restaurar.mutateAsync(lembrete.id)),
    })
  }

  return (
    <li
      className={cn(
        'grid gap-0.5 rounded-lg border bg-white p-3 text-sm shadow-xs transition-colors hover:border-foreground/25',
        lembrete.na_janela && 'border-amber-400 bg-amber-50/50',
      )}
    >
      <div className="flex items-start gap-1">
        <button
          type="button"
          onClick={onEditar}
          className={cn('flex-1 text-left font-medium break-words', FOCO_VISIVEL)}
        >
          {lembrete.titulo}
        </button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-xs" aria-label={`Ações de ${lembrete.titulo}`}>
              <Ellipsis />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={onEditar}>
              <Pencil /> Editar
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={darBaixa}>
              <CheckCheck /> Dar baixa
            </DropdownMenuItem>
            <DropdownMenuItem variant="destructive" onSelect={excluirLembrete}>
              <Trash2 /> Excluir
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <p className="text-xs text-muted-foreground">
        {data}
        {lembrete.recorrencia_descricao && ` · ${lembrete.recorrencia_descricao}`}
      </p>
      <p className={cn('text-xs', vencido ? 'font-medium text-red-600' : 'text-muted-foreground')}>
        {textoRelativo(lembrete.dias_restantes)}
        {/* RN-34: a interface só mostra a partir de 2. */}
        {lembrete.ocorrencias_atrasadas >= 2 &&
          ` · ${lembrete.ocorrencias_atrasadas} ocorrências atrasadas`}
      </p>
    </li>
  )
}
