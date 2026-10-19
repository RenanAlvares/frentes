import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import type { components } from '@/api/schema'

type AnotacaoCriar = components['schemas']['AnotacaoCriar']
type AnotacaoAtualizar = components['schemas']['AnotacaoAtualizar']

export function useAnotacoes(projetoId: string) {
  return useQuery({
    queryKey: chaves.anotacoes.lista(projetoId),
    queryFn: () =>
      exigir(
        client.GET('/api/projetos/{projeto_id}/anotacoes', {
          params: { path: { projeto_id: projetoId } },
        }),
      ),
  })
}

// 05 §4: anotação invalida a lista do projeto.
function useInvalidarAnotacoes(projetoId: string) {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: chaves.anotacoes.lista(projetoId) })
}

const caminho = (id: string) => ({ params: { path: { anotacao_id: id } } })

export function useCriarAnotacao(projetoId: string) {
  const invalidar = useInvalidarAnotacoes(projetoId)
  return useMutation({
    mutationFn: (dados: AnotacaoCriar) =>
      exigir(
        client.POST('/api/projetos/{projeto_id}/anotacoes', {
          params: { path: { projeto_id: projetoId } },
          body: dados,
        }),
      ),
    onSuccess: () => invalidar(),
  })
}

/** Salvar do modal e o "fixar" do card (ação direta, RN-85). */
export function useAtualizarAnotacao(projetoId: string) {
  const invalidar = useInvalidarAnotacoes(projetoId)
  return useMutation({
    mutationFn: ({ id, dados }: { id: string; dados: AnotacaoAtualizar }) =>
      exigir(client.PATCH('/api/anotacoes/{anotacao_id}', { ...caminho(id), body: dados })),
    onSuccess: () => invalidar(),
  })
}

export function useExcluirAnotacao(projetoId: string) {
  const invalidar = useInvalidarAnotacoes(projetoId)
  return useMutation({
    mutationFn: (id: string) => exigir(client.DELETE('/api/anotacoes/{anotacao_id}', caminho(id))),
    onSuccess: () => invalidar(),
  })
}

export function useRestaurarAnotacao(projetoId: string) {
  const invalidar = useInvalidarAnotacoes(projetoId)
  return useMutation({
    mutationFn: (id: string) =>
      exigir(
        client.POST('/api/lixeira/{tipo}/{item_id}/restaurar', {
          params: { path: { tipo: 'anotacao', item_id: id } },
        }),
      ),
    onSuccess: () => invalidar(),
  })
}
