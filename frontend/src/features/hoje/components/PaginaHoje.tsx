import { CircleCheckBig } from 'lucide-react'
import { useSearchParams } from 'react-router'
import { mensagemDoErro } from '@/api/erros'
import { EstadoVazio } from '@/components/comum/EstadoVazio'
import { Skeleton } from '@/components/ui/skeleton'
import { ItemHoje } from '@/features/hoje/components/ItemHoje'
import { LinhaAtrasadas } from '@/features/hoje/components/LinhaAtrasadas'
import { ModalTarefa } from '@/features/tarefas/components/ModalTarefa'
import { useTarefa, useTarefasHoje } from '@/features/tarefas/hooks/useTarefas'

/** Tarefas de hoje (01 §4.3; RN-60..62: as listas já vêm filtradas e ordenadas da API). */
export function PaginaHoje() {
  const { data, isPending, isError, error } = useTarefasHoje()
  // `?tarefa=:id` abre o modal da tarefa aqui mesmo, sobre a lista.
  const [parametros, setParametros] = useSearchParams()
  const tarefaAberta = parametros.get('tarefa') ?? undefined
  const { data: detalhe } = useTarefa(tarefaAberta)
  const daLista = [...(data?.atrasadas ?? []), ...(data?.hoje ?? [])].find(
    (tarefa) => tarefa.id === tarefaAberta,
  )
  const projetoId = daLista?.projeto.id ?? detalhe?.projeto_id

  const trocarTarefa = (tarefaId: string | null) =>
    setParametros(
      (atuais) => {
        if (tarefaId) atuais.set('tarefa', tarefaId)
        else atuais.delete('tarefa')
        return atuais
      },
      { replace: true },
    )

  return (
    <div className="mx-auto grid max-w-3xl gap-6">
      <h1 className="text-xl font-semibold">Tarefas de hoje</h1>
      {isPending ? (
        <div className="grid gap-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-12 rounded-lg" />
          ))}
        </div>
      ) : isError ? (
        <p role="alert" className="text-sm text-red-600">
          {mensagemDoErro(error)}
        </p>
      ) : (
        <>
          <LinhaAtrasadas tarefas={data.atrasadas} onAbrir={trocarTarefa} />
          <section aria-labelledby="titulo-hoje" className="grid gap-2">
            <h2 id="titulo-hoje" className="font-semibold">
              Hoje
            </h2>
            {data.hoje.length === 0 ? (
              <EstadoVazio icone={CircleCheckBig} titulo="Nada para hoje. Bom trabalho." />
            ) : (
              <ul className="grid gap-2">
                {data.hoje.map((tarefa) => (
                  <ItemHoje key={tarefa.id} tarefa={tarefa} onAbrir={trocarTarefa} />
                ))}
              </ul>
            )}
          </section>
        </>
      )}
      {projetoId && (
        <ModalTarefa
          projetoId={projetoId}
          aberto={tarefaAberta !== undefined}
          tarefaId={tarefaAberta}
          onFechar={() => trocarTarefa(null)}
        />
      )}
    </div>
  )
}
