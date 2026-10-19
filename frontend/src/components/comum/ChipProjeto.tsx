import type { components } from '@/api/schema'
import { CORES_PROJETO } from '@/lib/cores'
import { cn } from '@/lib/utils'

type Props = { projeto: components['schemas']['ProjetoRef']; className?: string }

/** Chip do projeto com a cor dele (avisos e Tarefas de hoje, 01 §4.1 e §4.3). */
export function ChipProjeto({ projeto, className }: Props) {
  return (
    <span
      className={cn(
        'inline-flex max-w-48 items-center gap-1 rounded-full border px-2 py-0.5 text-xs',
        className,
      )}
    >
      <span className={cn('size-2 shrink-0 rounded-full', CORES_PROJETO[projeto.cor].fundo)} />
      <span className="truncate">{projeto.nome}</span>
    </span>
  )
}
