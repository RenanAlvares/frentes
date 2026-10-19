import { useSortable } from '@dnd-kit/sortable'
import { ArrowDown, ArrowUp, Minus, Plus, Repeat } from 'lucide-react'
import type { ReactNode, SyntheticEvent } from 'react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { TextoPrazo } from '@/components/comum/TextoPrazo'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useConcluirTarefa, useMenosUm } from '@/features/tarefas/hooks/useTarefas'
import type { Tarefa } from '@/features/tarefas/quadro'
import { cn } from '@/lib/utils'

type Props = { tarefa: Tarefa; hoje: string | undefined }

/**
 * Card arrastável do quadro (RN-25): mouse com limiar de 5 px e teclado com Espaço.
 * Clique ou Enter abre o modal da tarefa (depois de um arraste o dnd-kit descarta o clique).
 */
export function CardTarefa({ tarefa, hoje, onAbrir }: Props & { onAbrir: () => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: tarefa.id,
  })
  return (
    <div
      ref={setNodeRef}
      style={{
        transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
        transition,
      }}
      className={cn(
        'cursor-grab rounded-lg outline-none focus-visible:ring-3 focus-visible:ring-ring/50',
        isDragging && 'opacity-40',
      )}
      {...attributes}
      {...listeners}
      onClick={onAbrir}
      onKeyDown={(evento) => {
        listeners?.onKeyDown?.(evento)
        if (evento.key === 'Enter') {
          // Sem isto, o mesmo Enter ativa o primeiro botão do modal (o X) e o fecha na hora.
          evento.preventDefault()
          onAbrir()
        }
      }}
    >
      <ConteudoCard tarefa={tarefa} hoje={hoje} acoes={<AcoesMeta tarefa={tarefa} />} />
    </div>
  )
}

/** Visual do card; também usado na sobreposição do arraste (sem as ações). */
export function ConteudoCard({ tarefa, hoje, acoes }: Props & { acoes?: ReactNode }) {
  const meta = tarefa.tipo === 'meta_mensal'
  return (
    <article className="flex flex-col gap-1.5 rounded-lg border bg-white p-3 text-sm shadow-xs">
      <div className="flex items-start gap-1.5">
        <IconePrioridade prioridade={tarefa.prioridade} />
        <p className="flex-1 leading-snug break-words">{tarefa.titulo}</p>
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        {tarefa.prazo && <TextoPrazo prazo={tarefa.prazo} hoje={hoje} vencido={tarefa.atrasada} />}
        {/* 01 §4.4: selo "repete" ou "meta 2/4". */}
        {tarefa.tipo === 'repetida' && (
          <Badge variant="outline" title={tarefa.recorrencia_descricao ?? undefined}>
            <Repeat /> repete
          </Badge>
        )}
        {meta && (
          <Badge variant="outline">
            meta {tarefa.progresso_mes ?? 0}/{tarefa.meta_mensal}
          </Badge>
        )}
        {meta && acoes}
      </div>
    </article>
  )
}

/** Não deixa o clique/teclado/arraste dos botões chegarem ao card (que abre o modal e arrasta). */
const isolar = {
  onClick: (evento: SyntheticEvent) => evento.stopPropagation(),
  onKeyDown: (evento: SyntheticEvent) => evento.stopPropagation(),
  onPointerDown: (evento: SyntheticEvent) => evento.stopPropagation(),
}

/** RN-24: "+1" e "−1" direto no card de meta (01 §4.4); salvam na hora (RN-85). */
function AcoesMeta({ tarefa }: { tarefa: Tarefa }) {
  const maisUm = useConcluirTarefa(tarefa.projeto_id)
  const menosUm = useMenosUm(tarefa.projeto_id)
  const avisarErro = { onError: (erro: unknown) => toast.error(mensagemDoErro(erro)) }
  return (
    <div className="ml-auto flex gap-1" {...isolar}>
      <Button
        variant="outline"
        size="icon-xs"
        aria-label={`−1 em ${tarefa.titulo}`}
        disabled={!tarefa.progresso_mes || menosUm.isPending}
        onClick={() => menosUm.mutate(tarefa.id, avisarErro)}
      >
        <Minus />
      </Button>
      <Button
        variant="outline"
        size="icon-xs"
        aria-label={`+1 em ${tarefa.titulo}`}
        disabled={maisUm.isPending}
        onClick={() => maisUm.mutate(tarefa.id, avisarErro)}
      >
        <Plus />
      </Button>
    </div>
  )
}

/** 05 §5: alta = seta vermelha para cima; baixa = seta cinza para baixo; média sem ícone. */
function IconePrioridade({ prioridade }: { prioridade: Tarefa['prioridade'] }) {
  if (prioridade === 'alta') {
    return (
      <ArrowUp
        role="img"
        aria-label="Prioridade alta"
        className="mt-0.5 size-4 shrink-0 text-red-600"
      />
    )
  }
  if (prioridade === 'baixa') {
    return (
      <ArrowDown
        role="img"
        aria-label="Prioridade baixa"
        className="mt-0.5 size-4 shrink-0 text-muted-foreground"
      />
    )
  }
  return null
}
