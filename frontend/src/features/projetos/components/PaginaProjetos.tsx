import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  rectSortingStrategy,
  SortableContext,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable'
import { FolderKanban, Plus } from 'lucide-react'
import { useState } from 'react'
import { mensagemDoErro } from '@/api/erros'
import { useSaude } from '@/app/layout/useSaude'
import { EstadoVazio } from '@/components/comum/EstadoVazio'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { CardProjeto } from '@/features/projetos/components/CardProjeto'
import { ModalProjeto } from '@/features/projetos/components/ModalProjeto'
import {
  useExcluirComDesfazer,
  useProjetos,
  useReordenarProjetos,
} from '@/features/projetos/hooks/useProjetos'

const GRADE = 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'

/** Home (01 §4.2): projetos ativos (RN-12, RN-17) na ordem de RN-15. */
export function PaginaProjetos() {
  const { data: projetos, isPending, isError, error } = useProjetos()
  const { data: saude } = useSaude()
  const reordenar = useReordenarProjetos()
  const excluirProjeto = useExcluirComDesfazer()
  const [modal, setModal] = useState<{ aberto: boolean; projetoId?: string }>({ aberto: false })
  const sensores = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const novoProjeto = () => setModal({ aberto: true })

  function aoSoltar({ active, over }: DragEndEvent) {
    if (!projetos || !over || active.id === over.id) return
    const ids = projetos.map((projeto) => projeto.id)
    reordenar.mutate(arrayMove(ids, ids.indexOf(String(active.id)), ids.indexOf(String(over.id))))
  }

  return (
    <section className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Projetos</h1>
      {isPending ? (
        <div className={GRADE} aria-busy="true">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-40 rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <p role="alert" className="text-destructive">
          {mensagemDoErro(error)}
        </p>
      ) : projetos.length === 0 ? (
        <EstadoVazio icone={FolderKanban} titulo="Crie seu primeiro projeto">
          <Button onClick={novoProjeto}>
            <Plus /> Novo projeto
          </Button>
        </EstadoVazio>
      ) : (
        <DndContext sensors={sensores} collisionDetection={closestCenter} onDragEnd={aoSoltar}>
          <SortableContext items={projetos.map((p) => p.id)} strategy={rectSortingStrategy}>
            <div className={GRADE}>
              {projetos.map((projeto) => (
                <CardProjeto
                  key={projeto.id}
                  projeto={projeto}
                  hoje={saude?.hoje}
                  onEditar={() => setModal({ aberto: true, projetoId: projeto.id })}
                  onExcluir={() => excluirProjeto(projeto.id)}
                />
              ))}
              <button
                type="button"
                onClick={novoProjeto}
                className="flex min-h-40 items-center justify-center gap-2 rounded-xl border-2 border-dashed text-muted-foreground transition-colors outline-none hover:border-foreground/40 hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <Plus className="size-4" /> Novo projeto
              </button>
            </div>
          </SortableContext>
        </DndContext>
      )}
      <ModalProjeto
        aberto={modal.aberto}
        projetoId={modal.projetoId}
        onFechar={() => setModal({ aberto: false })}
      />
    </section>
  )
}
