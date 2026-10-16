import { Bell, Folder, FolderX, SquareCheck, StickyNote } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import { ErroApi, mensagemDoErro } from '@/api/erros'
import { EstadoVazio } from '@/components/comum/EstadoVazio'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { AreaProjeto } from '@/features/projetos/components/AreaProjeto'
import { CabecalhoProjeto } from '@/features/projetos/components/CabecalhoProjeto'
import { useProjeto } from '@/features/projetos/hooks/useProjetos'
import { ModalTarefa } from '@/features/tarefas/components/ModalTarefa'
import { QuadroTarefas } from '@/features/tarefas/components/QuadroTarefas'

function EmBreve() {
  return <p className="px-1 text-sm text-muted-foreground">Em breve.</p>
}

/**
 * Projeto aberto (01 §4.4). Layout de 05 §7:
 * ≥ 1280 px: Lembretes 280 | Tarefas | Documentos + Anotações 300;
 * 768–1279: Tarefas em cima e as outras duas lado a lado; < 768: tudo empilhado.
 */
export function PaginaProjeto() {
  const { id = '' } = useParams()
  const { data: projeto, isPending, isError, error } = useProjeto(id)
  // 01 §3: `?tarefa=:id` abre o modal da tarefa (link direto também funciona).
  const [parametros, setParametros] = useSearchParams()
  const tarefaAberta = parametros.get('tarefa') ?? undefined
  const [criandoTarefa, setCriandoTarefa] = useState(false)

  const trocarTarefa = (tarefaId: string | null) =>
    setParametros(
      (atuais) => {
        if (tarefaId) atuais.set('tarefa', tarefaId)
        else atuais.delete('tarefa')
        return atuais
      },
      { replace: true },
    )

  if (isPending) return <Skeleton className="h-32 rounded-xl" />
  if (isError) {
    if (error instanceof ErroApi && error.status === 404) {
      return (
        <EstadoVazio icone={FolderX} titulo="Projeto não encontrado.">
          <Button variant="outline" asChild>
            <Link to="/">Voltar para Projetos</Link>
          </Button>
        </EstadoVazio>
      )
    }
    return (
      <p role="alert" className="text-destructive">
        {mensagemDoErro(error)}
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <CabecalhoProjeto projeto={projeto} />
      <div className="grid items-start gap-4 md:grid-cols-2 xl:grid-cols-[280px_minmax(0,1fr)_300px]">
        <AreaProjeto
          area="tarefas"
          titulo="Tarefas"
          icone={SquareCheck}
          className="md:col-span-2 xl:col-span-1 xl:col-start-2 xl:row-start-1"
        >
          <QuadroTarefas
            projetoId={projeto.id}
            onAbrirTarefa={trocarTarefa}
            onNovaTarefa={() => setCriandoTarefa(true)}
          />
        </AreaProjeto>
        <AreaProjeto
          area="lembretes"
          titulo="Lembretes"
          icone={Bell}
          className="xl:col-start-1 xl:row-start-1"
        >
          <EmBreve />
        </AreaProjeto>
        <div className="flex min-w-0 flex-col gap-4 xl:col-start-3 xl:row-start-1">
          <AreaProjeto area="documentos" titulo="Documentos" icone={Folder}>
            <EmBreve />
          </AreaProjeto>
          <AreaProjeto area="anotacoes" titulo="Anotações" icone={StickyNote}>
            <EmBreve />
          </AreaProjeto>
        </div>
      </div>
      <ModalTarefa
        projetoId={projeto.id}
        aberto={tarefaAberta !== undefined || criandoTarefa}
        tarefaId={tarefaAberta}
        onFechar={() => {
          setCriandoTarefa(false)
          trocarTarefa(null)
        }}
      />
    </div>
  )
}
