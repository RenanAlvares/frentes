import {
  closestCorners,
  defaultDropAnimationSideEffects,
  DndContext,
  DragOverlay,
  KeyboardSensor,
  MeasuringStrategy,
  PointerSensor,
  useSensor,
  useSensors,
  type Active,
  type Announcements,
  type DragEndEvent,
  type DragOverEvent,
  type DropAnimation,
  type Over,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { useState } from 'react'
import { mensagemDoErro } from '@/api/erros'
import { useSaude } from '@/app/layout/useSaude'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ConteudoCard } from '@/features/tarefas/components/CardTarefa'
import { ColunaQuadro } from '@/features/tarefas/components/ColunaQuadro'
import { CriacaoRapida } from '@/features/tarefas/components/CriacaoRapida'
import { DialogoConcluidas } from '@/features/tarefas/components/DialogoConcluidas'
import { useMoverTarefa, useQuadro } from '@/features/tarefas/hooks/useTarefas'
import {
  aplicarNoQuadro,
  colunaDe,
  COLUNAS,
  colunasDoQuadro,
  pedidoDeMover,
  reposicionar,
  ROTULO_COLUNA,
  type Colunas,
} from '@/features/tarefas/quadro'

/** Soltar: o card flutuante pousa no lugar novo com uma curva suave; o card real fica oculto até lá. */
const ANIMACAO_SOLTAR: DropAnimation = {
  duration: 220,
  easing: 'cubic-bezier(0.25, 1, 0.5, 1)',
  sideEffects: defaultDropAnimationSideEffects({ styles: { active: { opacity: '0' } } }),
}

/** O item arrastado passou da metade do item de destino? (cair antes ou depois dele) */
function depoisDe(active: Active, over: Over): boolean {
  const arrastado = active.rect.current.translated
  return arrastado
    ? arrastado.top + arrastado.height / 2 > over.rect.top + over.rect.height / 2
    : false
}

type Props = {
  projetoId: string
  /** Clique ou Enter no card (abre o modal da tarefa). */
  onAbrirTarefa: (tarefaId: string) => void
  /** Botão "Nova tarefa" da criação rápida. */
  onNovaTarefa: () => void
}

/** 01 §4.4 e 05 §8: três colunas; soltar chama `mover` com `status` e `indice` (RN-25). */
export function QuadroTarefas({ projetoId, onAbrirTarefa, onNovaTarefa }: Props) {
  const { data: quadro, isPending, isError, error } = useQuadro(projetoId)
  const { data: saude } = useSaude()
  const mover = useMoverTarefa(projetoId)
  // Arrumação local enquanto arrasta (a tarefa já aparece na coluna sob o cursor).
  const [arrastando, setArrastando] = useState<{ id: string; colunas: Colunas } | null>(null)
  const [verTodas, setVerTodas] = useState(false)
  // Depois de soltar, a arrumação nova fica na tela até o cache trazer o quadro previsto. Sem
  // isso o card volta um quadro para a coluna antiga e a animação de soltar vai para lá.
  const [aplicando, setAplicando] = useState<Colunas | null>(null)
  const [quadroVisto, setQuadroVisto] = useState(quadro)
  if (quadro !== quadroVisto) {
    setQuadroVisto(quadro)
    setAplicando(null)
  }
  const sensores = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    // Só Espaço inicia o arraste pelo teclado; Enter fica para abrir a tarefa (1.6).
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
      keyboardCodes: { start: ['Space'], cancel: ['Escape'], end: ['Space'] },
    }),
  )

  if (isPending) return <Skeleton className="h-64 rounded-lg" />
  if (isError) {
    return (
      <p role="alert" className="text-destructive">
        {mensagemDoErro(error)}
      </p>
    )
  }

  const tarefas = new Map(
    [...quadro.pendente, ...quadro.em_andamento, ...quadro.concluida].map((t) => [t.id, t]),
  )
  const colunas = arrastando?.colunas ?? aplicando ?? colunasDoQuadro(quadro)
  const titulo = (id: string | number) => tarefas.get(String(id))?.titulo ?? 'tarefa'
  const ativa = arrastando ? tarefas.get(arrastando.id) : undefined

  function aoPassar({ active, over }: DragOverEvent) {
    if (!over || !arrastando) return
    const id = String(active.id)
    const alvo = String(over.id)
    if (colunaDe(arrastando.colunas, id) === colunaDe(arrastando.colunas, alvo)) return
    // RN-24: meta não troca de coluna (só reordena dentro da sua).
    if (tarefas.get(id)?.tipo === 'meta_mensal') return
    setArrastando({
      id,
      colunas: reposicionar(arrastando.colunas, id, alvo, depoisDe(active, over)),
    })
  }

  const aoSoltar = ({ active, over }: DragEndEvent) => {
    const atual = arrastando?.colunas
    setArrastando(null)
    if (!over || !atual) return
    const id = String(active.id)
    const alvo = String(over.id)
    let final = atual
    const coluna = colunaDe(atual, id)
    if (coluna && coluna === colunaDe(atual, alvo) && coluna !== alvo) {
      // Mesma coluna: como arrayMove (descendo fica depois do alvo, subindo fica antes).
      const lista = atual[coluna]
      final = reposicionar(atual, id, alvo, lista.indexOf(id) < lista.indexOf(alvo))
    }
    const pedido = pedidoDeMover(final, id)
    const antes = pedidoDeMover(colunasDoQuadro(quadro), id)
    if (!pedido || (antes && antes.status === pedido.status && antes.indice === pedido.indice))
      return
    // RN-23: repetida solta em Concluída continua em Pendente (com o próximo prazo, da API).
    const repetida = tarefas.get(id)?.tipo === 'repetida' && pedido.status === 'concluida'
    const previsto = repetida ? quadro : aplicarNoQuadro(quadro, final, id)
    if (!repetida) setAplicando(final)
    mover.mutate({ tarefaId: id, ...pedido, previsto })
  }

  const anuncios: Announcements = {
    onDragStart: ({ active }) => `Movendo "${titulo(active.id)}".`,
    onDragOver: ({ active, over }) =>
      over ? `"${titulo(active.id)}" sobre ${descrever(over.id)}.` : undefined,
    onDragEnd: ({ active, over }) =>
      over ? `"${titulo(active.id)}" solta em ${descrever(over.id)}.` : 'Movimento cancelado.',
    onDragCancel: ({ active }) => `Movimento de "${titulo(active.id)}" cancelado.`,
  }
  function descrever(id: string | number) {
    const coluna = colunaDe(colunas, String(id))
    return coluna && String(id) === coluna ? `a coluna ${ROTULO_COLUNA[coluna]}` : `"${titulo(id)}"`
  }

  return (
    <div className="flex flex-col gap-3">
      <CriacaoRapida projetoId={projetoId} onNovaTarefa={onNovaTarefa} />
      <DndContext
        sensors={sensores}
        collisionDetection={closestCorners}
        // Mede as colunas durante o arraste: trocar de coluna não dá saltos.
        measuring={{ droppable: { strategy: MeasuringStrategy.Always } }}
        accessibility={{
          announcements: anuncios,
          screenReaderInstructions: {
            draggable:
              'Para mover a tarefa, pressione Espaço, use as setas para escolher o lugar e Espaço de novo para soltar. Esc cancela.',
          },
        }}
        onDragStart={({ active }) =>
          setArrastando({ id: String(active.id), colunas: colunasDoQuadro(quadro) })
        }
        onDragOver={aoPassar}
        onDragEnd={aoSoltar}
        onDragCancel={() => setArrastando(null)}
      >
        <div className="flex gap-3 overflow-x-auto pb-1">
          {COLUNAS.map((status) => {
            const lista = colunas[status].flatMap((id) => tarefas.get(id) ?? [])
            const concluida = status === 'concluida'
            return (
              <ColunaQuadro
                key={status}
                status={status}
                tarefas={lista}
                total={concluida ? quadro.total_concluidas : lista.length}
                hoje={saude?.hoje}
                onAbrir={onAbrirTarefa}
                rodape={
                  concluida && quadro.total_concluidas > quadro.concluida.length ? (
                    <Button variant="ghost" size="sm" onClick={() => setVerTodas(true)}>
                      Ver todas ({quadro.total_concluidas})
                    </Button>
                  ) : undefined
                }
              />
            )
          })}
        </div>
        <DragOverlay dropAnimation={ANIMACAO_SOLTAR}>
          {ativa ? (
            // O card "levantado": leve inclinação e sombra enquanto acompanha o cursor.
            <div className="rotate-2 cursor-grabbing rounded-lg shadow-xl">
              <ConteudoCard tarefa={ativa} hoje={saude?.hoje} />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
      <DialogoConcluidas
        projetoId={projetoId}
        aberto={verTodas}
        onFechar={() => setVerTodas(false)}
      />
    </div>
  )
}
