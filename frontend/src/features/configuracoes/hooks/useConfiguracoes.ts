import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import type { components } from '@/api/schema'

export type Configuracoes = components['schemas']['Configuracoes']
type ConfiguracoesAtualizar = components['schemas']['ConfiguracoesAtualizar']

export function useConfiguracoes() {
  return useQuery({
    queryKey: chaves.configuracoes(),
    queryFn: () => exigir(client.GET('/api/configuracoes')),
  })
}

/** RN-100: `aviso_tarefas_dias` muda os avisos e o contador de avisos dos projetos. */
export function useAtualizarConfiguracoes() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dados: ConfiguracoesAtualizar) =>
      exigir(client.PATCH('/api/configuracoes', { body: dados })),
    onSuccess: (configuracoes) => {
      queryClient.setQueryData(chaves.configuracoes(), configuracoes)
      return Promise.all([
        queryClient.invalidateQueries({ queryKey: chaves.avisos() }),
        queryClient.invalidateQueries({ queryKey: chaves.projetos.todos() }),
      ])
    },
  })
}
