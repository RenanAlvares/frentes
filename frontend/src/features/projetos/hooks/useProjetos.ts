import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import { mensagemDoErro } from '@/api/erros'
import type { components } from '@/api/schema'

type ProjetoResumo = components['schemas']['ProjetoResumo']
type ProjetoCriar = components['schemas']['ProjetoCriar']
type ProjetoAtualizar = components['schemas']['ProjetoAtualizar']

export function useProjetos(arquivados = false) {
  return useQuery({
    queryKey: chaves.projetos.lista(arquivados),
    queryFn: () => exigir(client.GET('/api/projetos', { params: { query: { arquivados } } })),
  })
}

export function useProjeto(id: string | undefined) {
  return useQuery({
    queryKey: chaves.projetos.detalhe(id ?? ''),
    queryFn: () =>
      exigir(client.GET('/api/projetos/{projeto_id}', { params: { path: { projeto_id: id! } } })),
    enabled: id !== undefined,
  })
}

// 05 §4: qualquer mutação de projeto invalida `projetos.*` (avisos e hoje entram nas fases 3).
function useInvalidarProjetos() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: chaves.projetos.todos() })
}

export function useCriarProjeto() {
  const invalidar = useInvalidarProjetos()
  return useMutation({
    mutationFn: (dados: ProjetoCriar) => exigir(client.POST('/api/projetos', { body: dados })),
    onSuccess: invalidar,
  })
}

export function useAtualizarProjeto() {
  const invalidar = useInvalidarProjetos()
  return useMutation({
    mutationFn: ({ id, dados }: { id: string; dados: ProjetoAtualizar }) =>
      exigir(
        client.PATCH('/api/projetos/{projeto_id}', {
          params: { path: { projeto_id: id } },
          body: dados,
        }),
      ),
    onSuccess: invalidar,
  })
}

export function useExcluirProjeto() {
  const invalidar = useInvalidarProjetos()
  return useMutation({
    mutationFn: (id: string) =>
      exigir(client.DELETE('/api/projetos/{projeto_id}', { params: { path: { projeto_id: id } } })),
    onSuccess: invalidar,
  })
}

/** Desfazer da exclusão (RN-92). */
export function useRestaurarProjeto() {
  const invalidar = useInvalidarProjetos()
  return useMutation({
    mutationFn: (id: string) =>
      exigir(
        client.POST('/api/lixeira/{tipo}/{item_id}/restaurar', {
          params: { path: { tipo: 'projeto', item_id: id } },
        }),
      ),
    onSuccess: invalidar,
  })
}

/** RN-15, otimista (05 §4): a grade muda na hora e volta se a API recusar. */
export function useReordenarProjetos() {
  const queryClient = useQueryClient()
  const chave = chaves.projetos.lista(false)
  return useMutation({
    mutationFn: (ids: string[]) => exigir(client.PUT('/api/projetos/ordem', { body: { ids } })),
    onMutate: async (ids) => {
      await queryClient.cancelQueries({ queryKey: chave })
      const anterior = queryClient.getQueryData<ProjetoResumo[]>(chave)
      if (anterior) {
        const porId = new Map(anterior.map((projeto) => [projeto.id, projeto]))
        const nova = ids.flatMap((id, posicao) => {
          const projeto = porId.get(id)
          return projeto ? [{ ...projeto, posicao }] : []
        })
        queryClient.setQueryData(chave, nova)
      }
      return { anterior }
    },
    onError: (erro, _ids, contexto) => {
      queryClient.setQueryData(chave, contexto?.anterior)
      toast.error(mensagemDoErro(erro))
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: chaves.projetos.todos() }),
  })
}
