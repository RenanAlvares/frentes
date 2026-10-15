import { useSortable } from '@dnd-kit/sortable'
import { Ellipsis, GripVertical, Pencil, Trash2 } from 'lucide-react'
import { Link } from 'react-router'
import type { components } from '@/api/schema'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ROTULO_STATUS } from '@/features/projetos/status'
import { CORES_PROJETO } from '@/lib/cores'
import { anoDe, antesDe, formatarData, formatarDataCurta } from '@/lib/datas'
import { cn } from '@/lib/utils'

type ProjetoResumo = components['schemas']['ProjetoResumo']

type Props = {
  projeto: ProjetoResumo
  /** "Hoje" da API (RN-01); sem ele o prazo não é marcado como vencido. */
  hoje: string | undefined
  onEditar: () => void
  onExcluir: () => void
}

/** 01 §4.2. Arrasta pela alça (RN-15); o resto do card abre o projeto. */
export function CardProjeto({ projeto, hoje, onEditar, onExcluir }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: projeto.id })
  const vencido = Boolean(projeto.prazo && hoje && antesDe(projeto.prazo, hoje))
  // Sem o "hoje" da API ainda, mostra a data completa (não sabe qual é o ano atual).
  const textoPrazo = (prazo: string) =>
    hoje ? formatarDataCurta(prazo, anoDe(hoje)) : formatarData(prazo)

  return (
    <article
      ref={setNodeRef}
      style={{
        transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
        transition,
      }}
      className={cn(
        'relative flex flex-col overflow-hidden rounded-xl border bg-white transition-shadow hover:shadow-sm',
        isDragging && 'z-20 shadow-lg',
      )}
    >
      <div className={cn('h-1.5', CORES_PROJETO[projeto.cor].fundo)} />
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-start gap-1">
          <h2 className="flex-1 font-semibold leading-snug">
            {/* O ::after estica o link sobre o card inteiro; alça e menu ficam por cima. */}
            <Link
              to={`/projetos/${projeto.id}`}
              className="outline-none after:absolute after:inset-0 focus-visible:underline"
            >
              {projeto.nome}
            </Link>
          </h2>
          <Button
            ref={setActivatorNodeRef}
            variant="ghost"
            size="icon-sm"
            aria-label={`Arrastar ${projeto.nome}`}
            className="relative z-10 cursor-grab text-muted-foreground active:cursor-grabbing"
            {...attributes}
            {...listeners}
          >
            <GripVertical />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label={`Ações de ${projeto.nome}`}
                className="relative z-10"
              >
                <Ellipsis />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onSelect={onEditar}>
                <Pencil /> Editar
              </DropdownMenuItem>
              <DropdownMenuItem variant="destructive" onSelect={onExcluir}>
                <Trash2 /> Excluir
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <Badge variant="secondary">{ROTULO_STATUS[projeto.status]}</Badge>
        {projeto.prazo && (
          <p className={cn('text-sm', vencido ? 'text-red-600' : 'text-muted-foreground')}>
            Prazo {textoPrazo(projeto.prazo)}
          </p>
        )}
        {projeto.progresso && <BarraProgresso {...projeto.progresso} />}
        {projeto.avisos > 0 && (
          <p className="text-sm font-medium text-amber-600">
            {projeto.avisos} {projeto.avisos === 1 ? 'aviso' : 'avisos'}
          </p>
        )}
      </div>
    </article>
  )
}

/** RN-13: total 0 → barra vazia e "Sem tarefas". */
function BarraProgresso({ concluidas, total }: components['schemas']['Progresso']) {
  const percentual = total > 0 ? Math.round((concluidas / total) * 100) : 0
  return (
    <div className="flex flex-col gap-1">
      <div
        role="progressbar"
        aria-label="Progresso"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percentual}
        className="h-1.5 overflow-hidden rounded-full bg-muted"
      >
        <div className="h-full bg-foreground/70" style={{ width: `${percentual}%` }} />
      </div>
      <p className="text-xs text-muted-foreground">
        {total > 0 ? `${concluidas}/${total} tarefas` : 'Sem tarefas'}
      </p>
    </div>
  )
}
