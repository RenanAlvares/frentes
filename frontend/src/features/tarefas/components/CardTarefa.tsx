import { useSortable } from '@dnd-kit/sortable'
import { ArrowDown, ArrowUp } from 'lucide-react'
import { TextoPrazo } from '@/components/comum/TextoPrazo'
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
        if (evento.key === 'Enter') onAbrir()
      }}
    >
      <ConteudoCard tarefa={tarefa} hoje={hoje} />
    </div>
  )
}

/** Visual do card; também usado na sobreposição do arraste. */
export function ConteudoCard({ tarefa, hoje }: Props) {
  return (
    <article className="flex flex-col gap-1.5 rounded-lg border bg-white p-3 text-sm shadow-xs">
      <div className="flex items-start gap-1.5">
        <IconePrioridade prioridade={tarefa.prioridade} />
        <p className="flex-1 leading-snug break-words">{tarefa.titulo}</p>
      </div>
      {tarefa.prazo && <TextoPrazo prazo={tarefa.prazo} hoje={hoje} vencido={tarefa.atrasada} />}
    </article>
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
