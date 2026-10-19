import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import type { components } from '@/api/schema'

type LembreteCriar = components['schemas']['LembreteCriar']
type LembreteAtualizar = components['schemas']['LembreteAtualizar']

export function useLembretes(projetoId: string) {
  return useQuery({
    queryKey: chaves.lembretes.lista(projetoId),
    queryFn: () =>
      exigir(
        client.GET('/api/projetos/{projeto_id}/lembretes', {
          params: { path: { projeto_id: projetoId } },
        }),
      ),
  })
}

// 05 §4: lembrete (qualquer) invalida a lista do projeto e os projetos (contador de avisos).
// `avisos()` entra junto com o painel de avisos (3.4).
function useInvalidarLembretes(projetoId: string) {
  const queryClient = useQueryClient()
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: chaves.lembretes.lista(projetoId) }),
      queryClient.invalidateQueries({ queryKey: chaves.projetos.todos() }),
    ])
}

export function useCriarLembrete(projetoId: string) {
  const invalidar = useInvalidarLembretes(projetoId)
  return useMutation({
    mutationFn: (dados: LembreteCriar) =>
      exigir(
        client.POST('/api/projetos/{projeto_id}/lembretes', {
          params: { path: { projeto_id: projetoId } },
          body: dados,
        }),
      ),
    onSuccess: () => invalidar(),
  })
}

export function useAtualizarLembrete(projetoId: string) {
  const invalidar = useInvalidarLembretes(projetoId)
  return useMutation({
    mutationFn: ({ id, dados }: { id: string; dados: LembreteAtualizar }) =>
      exigir(
        client.PATCH('/api/lembretes/{lembrete_id}', {
          params: { path: { lembrete_id: id } },
          body: dados,
        }),
      ),
    onSuccess: () => invalidar(),
  })
}

/** Ações diretas (RN-85: salvam na hora). */
function useAcaoLembrete(projetoId: string, acao: (id: string) => Promise<unknown>) {
  const invalidar = useInvalidarLembretes(projetoId)
  return useMutation({ mutationFn: acao, onSuccess: () => invalidar() })
}

const caminho = (id: string) => ({ params: { path: { lembrete_id: id } } })

/** RN-43. */
export const useDarBaixa = (projetoId: string) =>
  useAcaoLembrete(projetoId, (id) =>
    exigir(client.POST('/api/lembretes/{lembrete_id}/baixa', caminho(id))),
  )

/** RN-44: também é o "Reativar" da seção Concluídos. */
export const useDesfazerBaixa = (projetoId: string) =>
  useAcaoLembrete(projetoId, (id) =>
    exigir(client.POST('/api/lembretes/{lembrete_id}/desfazer-baixa', caminho(id))),
  )

export const useExcluirLembrete = (projetoId: string) =>
  useAcaoLembrete(projetoId, (id) =>
    exigir(client.DELETE('/api/lembretes/{lembrete_id}', caminho(id))),
  )

export const useRestaurarLembrete = (projetoId: string) =>
  useAcaoLembrete(projetoId, (id) =>
    exigir(
      client.POST('/api/lixeira/{tipo}/{item_id}/restaurar', {
        params: { path: { tipo: 'lembrete', item_id: id } },
      }),
    ),
  )
