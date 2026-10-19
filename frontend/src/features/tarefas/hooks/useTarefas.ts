import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import { mensagemDoErro } from '@/api/erros'
import type { components } from '@/api/schema'
import type { Quadro } from '@/features/tarefas/quadro'

type TarefaCriar = components['schemas']['TarefaCriar']
type TarefaAtualizar = components['schemas']['TarefaAtualizar']
type TarefaMover = components['schemas']['TarefaMover']

export function useTarefa(id: string | undefined) {
  return useQuery({
    queryKey: chaves.tarefas.detalhe(id ?? ''),
    queryFn: () =>
      exigir(client.GET('/api/tarefas/{tarefa_id}', { params: { path: { tarefa_id: id! } } })),
    enabled: id !== undefined,
  })
}

/** RN-60..63: listas da tela Tarefas de hoje (e o contador da aba). */
export function useTarefasHoje() {
  return useQuery({
    queryKey: chaves.tarefas.hoje(),
    queryFn: () => exigir(client.GET('/api/tarefas/hoje')),
  })
}

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

// 05 §4: mutação de tarefa invalida o quadro, as concluídas, Tarefas de hoje, os avisos e os
// projetos (progresso).
function useInvalidarTarefas(projetoId: string) {
  const queryClient = useQueryClient()
  return (tarefaId?: string) =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: chaves.tarefas.quadro(projetoId) }),
      queryClient.invalidateQueries({ queryKey: chaves.tarefas.concluidas(projetoId) }),
      queryClient.invalidateQueries({ queryKey: chaves.tarefas.hoje() }),
      queryClient.invalidateQueries({ queryKey: chaves.avisos() }),
      queryClient.invalidateQueries({ queryKey: chaves.projetos.todos() }),
      tarefaId && queryClient.invalidateQueries({ queryKey: chaves.tarefas.detalhe(tarefaId) }),
    ])
}

export function useAtualizarTarefa(projetoId: string) {
  const invalidar = useInvalidarTarefas(projetoId)
  return useMutation({
    mutationFn: ({ id, dados }: { id: string; dados: TarefaAtualizar }) =>
      exigir(
        client.PATCH('/api/tarefas/{tarefa_id}', {
          params: { path: { tarefa_id: id } },
          body: dados,
        }),
      ),
    onSuccess: (_tarefa, { id }) => invalidar(id),
  })
}

/** Ações diretas do modal e do card (RN-85: salvam na hora). */
function useAcaoTarefa(projetoId: string, acao: (id: string) => Promise<unknown>) {
  const invalidar = useInvalidarTarefas(projetoId)
  return useMutation({ mutationFn: acao, onSuccess: (_resultado, id) => invalidar(id) })
}

const caminho = (id: string) => ({ params: { path: { tarefa_id: id } } })

export const useConcluirTarefa = (projetoId: string) =>
  useAcaoTarefa(projetoId, (id) =>
    exigir(client.POST('/api/tarefas/{tarefa_id}/concluir', caminho(id))),
  )

/** Meta mensal "−1" (RN-24); "+1" é o mesmo `concluir`. */
export const useMenosUm = (projetoId: string) =>
  useAcaoTarefa(projetoId, (id) =>
    exigir(client.POST('/api/tarefas/{tarefa_id}/execucoes/remover-ultima', caminho(id))),
  )

export const useDesfazerConclusao = (projetoId: string) =>
  useAcaoTarefa(projetoId, (id) =>
    exigir(client.POST('/api/tarefas/{tarefa_id}/desfazer-conclusao', caminho(id))),
  )

export const useExcluirTarefa = (projetoId: string) =>
  useAcaoTarefa(projetoId, (id) => exigir(client.DELETE('/api/tarefas/{tarefa_id}', caminho(id))))

export const useRestaurarTarefa = (projetoId: string) =>
  useAcaoTarefa(projetoId, (id) =>
    exigir(
      client.POST('/api/lixeira/{tipo}/{item_id}/restaurar', {
        params: { path: { tipo: 'tarefa', item_id: id } },
      }),
    ),
  )

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
    onSuccess: () => invalidar(),
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
    onSettled: () => invalidar(),
  })
}
