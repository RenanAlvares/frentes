import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import type { components } from '@/api/schema'

export type ItemLixeira = components['schemas']['ItemLixeira']
export type TipoItemLixeira = components['schemas']['TipoItemLixeira']

export function useLixeira() {
  return useQuery({
    queryKey: chaves.lixeira(),
    queryFn: () => exigir(client.GET('/api/lixeira')),
    // As exclusões acontecem em outras telas e não invalidam a lixeira: sempre buscar ao abrir.
    staleTime: 0,
  })
}

// 05 §4: restaurar invalida a lixeira e tudo do tipo restaurado (o item não diz o projeto,
// então vão as listas do tipo inteiro).
const RESTAURADOS: Record<TipoItemLixeira, readonly (readonly string[])[]> = {
  projeto: [chaves.projetos.todos(), chaves.avisos(), chaves.tarefas.hoje()],
  tarefa: [['tarefas'], chaves.projetos.todos(), chaves.avisos()],
  lembrete: [['lembretes'], chaves.projetos.todos(), chaves.avisos()],
  documento: [['documentos']],
  anotacao: [['anotacoes']],
}

type Alvo = { tipo: TipoItemLixeira; id: string }
const caminho = ({ tipo, id }: Alvo) => ({ params: { path: { tipo, item_id: id } } })

export function useRestaurarDaLixeira() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (alvo: Alvo) =>
      exigir(client.POST('/api/lixeira/{tipo}/{item_id}/restaurar', caminho(alvo))),
    onSuccess: (_resultado, { tipo }) =>
      Promise.all(
        [chaves.lixeira(), ...RESTAURADOS[tipo]].map((queryKey) =>
          queryClient.invalidateQueries({ queryKey }),
        ),
      ),
  })
}

/** RN-93: definitivo; o item some só da lixeira (não aparece em outra tela). */
export function useExcluirDaLixeira() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (alvo: Alvo) =>
      exigir(client.DELETE('/api/lixeira/{tipo}/{item_id}', caminho(alvo))),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: chaves.lixeira() }),
  })
}

export function useEsvaziarLixeira() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => exigir(client.DELETE('/api/lixeira')),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: chaves.lixeira() }),
  })
}
