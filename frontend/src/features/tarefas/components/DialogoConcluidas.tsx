import { mensagemDoErro } from '@/api/erros'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useConcluidas } from '@/features/tarefas/hooks/useTarefas'
import { formatarCarimbo } from '@/lib/datas'

type Props = { projetoId: string; aberto: boolean; onFechar: () => void }

/** "Ver todas (N)" da coluna Concluída (01 §4.4): todas, da mais recente para a mais antiga. */
export function DialogoConcluidas({ projetoId, aberto, onFechar }: Props) {
  const { data: tarefas, isPending, isError, error } = useConcluidas(projetoId, aberto)

  return (
    <Dialog open={aberto} onOpenChange={(abrir) => !abrir && onFechar()}>
      <DialogContent aria-describedby={undefined} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Tarefas concluídas</DialogTitle>
        </DialogHeader>
        {isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : isError ? (
          <p role="alert" className="text-destructive">
            {mensagemDoErro(error)}
          </p>
        ) : (
          <ul className="max-h-[60vh] divide-y overflow-y-auto">
            {tarefas.map((tarefa) => (
              <li
                key={tarefa.id}
                className="flex items-baseline justify-between gap-3 py-2 text-sm"
              >
                <span className="break-words">{tarefa.titulo}</span>
                {tarefa.concluida_em && (
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {formatarCarimbo(tarefa.concluida_em)}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  )
}
