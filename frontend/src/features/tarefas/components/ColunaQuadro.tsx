import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import type { ReactNode } from 'react'
import { CardTarefa } from '@/features/tarefas/components/CardTarefa'
import { ROTULO_COLUNA, type StatusTarefa, type Tarefa } from '@/features/tarefas/quadro'
import { cn } from '@/lib/utils'

type Props = {
  status: StatusTarefa
  tarefas: Tarefa[]
  /** Contador do título (Concluída mostra o total, não só as 20 exibidas). */
  total: number
  hoje: string | undefined
  onAbrir: (tarefaId: string) => void
  rodape?: ReactNode
}

/** Uma coluna do quadro. A área toda recebe tarefas, mesmo vazia. */
export function ColunaQuadro({ status, tarefas, total, hoje, onAbrir, rodape }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: status })
  return (
    <section
      aria-label={ROTULO_COLUNA[status]}
      className="flex w-64 shrink-0 flex-col gap-2 rounded-lg border bg-neutral-100 p-2 md:w-auto md:min-w-0 md:flex-1 md:shrink"
    >
      <h3 className="flex items-center justify-between px-1 text-sm font-medium">
        {ROTULO_COLUNA[status]}
        <span className="text-xs text-muted-foreground">{total}</span>
      </h3>
      <SortableContext items={tarefas.map((t) => t.id)} strategy={verticalListSortingStrategy}>
        <div
          ref={setNodeRef}
          className={cn(
            'flex min-h-20 flex-1 flex-col gap-2 rounded-md transition-colors',
            isOver && 'bg-muted',
          )}
        >
          {tarefas.map((tarefa) => (
            <CardTarefa
              key={tarefa.id}
              tarefa={tarefa}
              hoje={hoje}
              onAbrir={() => onAbrir(tarefa.id)}
            />
          ))}
        </div>
      </SortableContext>
      {rodape}
    </section>
  )
}
