import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import { mensagemDoErro } from '@/api/erros'
import type { components } from '@/api/schema'
import type { Quadro } from '@/features/tarefas/quadro'

type TarefaCriar = components['schemas']['TarefaCriar']
type TarefaMover = components['schemas']['TarefaMover']

export function useQuadro(projetoId: string) {
  return useQuery({
    queryKey: chaves.tarefas.quadro(projetoId),
    queryFn: () =>
      exigir(
        client.GET('/api/projetos/{projeto_id}/tarefas', {
          params: { path: { projeto_id: projetoId } },
        }),
      ),
  })
}

/** "Ver todas" da coluna Concluída. */
export function useConcluidas(projetoId: string, ativo: boolean) {
  return useQuery({
    queryKey: chaves.tarefas.concluidas(projetoId),
    queryFn: () =>
      exigir(
        client.GET('/api/projetos/{projeto_id}/tarefas/concluidas', {
          params: { path: { projeto_id: projetoId } },
        }),
      ),
    enabled: ativo,
  })
}

// 05 §4: mutação de tarefa invalida o quadro, as concluídas e os projetos (progresso).
// `tarefas.hoje()` e `avisos()` entram junto com essas telas (fase 3).
function useInvalidarTarefas(projetoId: string) {
  const queryClient = useQueryClient()
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: chaves.tarefas.quadro(projetoId) }),
      queryClient.invalidateQueries({ queryKey: chaves.tarefas.concluidas(projetoId) }),
      queryClient.invalidateQueries({ queryKey: chaves.projetos.todos() }),
    ])
}

export function useCriarTarefa(projetoId: string) {
  const invalidar = useInvalidarTarefas(projetoId)
  return useMutation({
    mutationFn: (dados: TarefaCriar) =>
      exigir(
        client.POST('/api/projetos/{projeto_id}/tarefas', {
          params: { path: { projeto_id: projetoId } },
          body: dados,
        }),
      ),
    onSuccess: invalidar,
  })
}

type Movimento = TarefaMover & { tarefaId: string; previsto: Quadro }

/** RN-25, otimista (05 §4): o quadro muda na hora e volta se a API recusar. */
export function useMoverTarefa(projetoId: string) {
  const queryClient = useQueryClient()
  const chave = chaves.tarefas.quadro(projetoId)
  const invalidar = useInvalidarTarefas(projetoId)
  return useMutation({
    mutationFn: ({ tarefaId, status, indice }: Movimento) =>
      exigir(
        client.POST('/api/tarefas/{tarefa_id}/mover', {
          params: { path: { tarefa_id: tarefaId } },
          body: { status, indice },
        }),
      ),
    onMutate: async ({ previsto }) => {
      await queryClient.cancelQueries({ queryKey: chave })
      const anterior = queryClient.getQueryData<Quadro>(chave)
      queryClient.setQueryData(chave, previsto)
      return { anterior }
    },
    onSuccess: (quadro) => queryClient.setQueryData(chave, quadro),
    onError: (erro, _movimento, contexto) => {
      queryClient.setQueryData(chave, contexto?.anterior)
      toast.error(mensagemDoErro(erro))
    },
    onSettled: invalidar,
  })
}
