import { ArrowUp } from 'lucide-react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import type { components } from '@/api/schema'
import { ChipProjeto } from '@/components/comum/ChipProjeto'
import { Checkbox } from '@/components/ui/checkbox'
import { useConcluirTarefa, useDesfazerConclusao } from '@/features/tarefas/hooks/useTarefas'
import { avisarComDesfazer } from '@/lib/desfazer'
import { cn, FOCO_VISIVEL } from '@/lib/utils'

export type TarefaHoje = components['schemas']['TarefaHoje']

type Props = { tarefa: TarefaHoje; onAbrir: (tarefaId: string) => void }

/** 01 §4.3: checkbox para concluir, título (abre o modal), chip, prioridade alta, "repete"/"meta". */
export function ItemHoje({ tarefa, onAbrir }: Props) {
  const concluir = useConcluirTarefa(tarefa.projeto.id)
  const desfazer = useDesfazerConclusao(tarefa.projeto.id)
  // Meta mensal: marcar é o "+1" (RN-24); o Desfazer apaga a execução (RN-26).
  const meta = tarefa.tipo === 'meta_mensal'

  // `mutateAsync`: a tarefa sai da lista antes da resposta chegar, e o toast tem de aparecer.
  async function marcar() {
    try {
      await concluir.mutateAsync(tarefa.id)
    } catch (erro) {
      toast.error(mensagemDoErro(erro))
      return
    }
    avisarComDesfazer(meta ? '+1 registrado' : 'Tarefa concluída', () =>
      desfazer.mutateAsync(tarefa.id),
    )
  }

  return (
    <li className="flex items-center gap-3 rounded-lg border bg-white p-3 text-sm">
      <Checkbox
        checked={false}
        disabled={concluir.isPending}
        aria-label={meta ? `+1 em ${tarefa.titulo}` : `Concluir ${tarefa.titulo}`}
        onCheckedChange={() => void marcar()}
      />
      <button
        type="button"
        onClick={() => onAbrir(tarefa.id)}
        className={cn('min-w-0 flex-1 text-left font-medium break-words', FOCO_VISIVEL)}
      >
        {tarefa.titulo}
      </button>
      <div className="flex shrink-0 flex-wrap items-center justify-end gap-2 text-xs text-muted-foreground">
        {tarefa.prioridade === 'alta' && (
          <ArrowUp role="img" aria-label="Prioridade alta" className="size-4 text-red-600" />
        )}
        {tarefa.tipo === 'repetida' && <span>repete</span>}
        {meta && (
          <span>
            meta {tarefa.progresso_mes ?? 0}/{tarefa.meta_mensal}
          </span>
        )}
        <ChipProjeto projeto={tarefa.projeto} />
      </div>
    </li>
  )
}
