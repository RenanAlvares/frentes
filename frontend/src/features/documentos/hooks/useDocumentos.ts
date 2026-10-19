import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import { mensagemDoErro } from '@/api/erros'
import { enviarArquivo } from '@/features/documentos/upload'

export function useDocumentos(projetoId: string) {
  return useQuery({
    queryKey: chaves.documentos.lista(projetoId),
    queryFn: () =>
      exigir(
        client.GET('/api/projetos/{projeto_id}/documentos', {
          params: { path: { projeto_id: projetoId } },
        }),
      ),
  })
}

// 05 §4: documento invalida a lista do projeto.
function useInvalidarDocumentos(projetoId: string) {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: chaves.documentos.lista(projetoId) })
}

const caminho = (id: string) => ({ params: { path: { documento_id: id } } })

/** RN-72: a API mantém a extensão original. */
export function useRenomearDocumento(projetoId: string) {
  const invalidar = useInvalidarDocumentos(projetoId)
  return useMutation({
    mutationFn: ({ id, nome }: { id: string; nome: string }) =>
      exigir(client.PATCH('/api/documentos/{documento_id}', { ...caminho(id), body: { nome } })),
    onSuccess: () => invalidar(),
  })
}

export function useExcluirDocumento(projetoId: string) {
  const invalidar = useInvalidarDocumentos(projetoId)
  return useMutation({
    mutationFn: (id: string) =>
      exigir(client.DELETE('/api/documentos/{documento_id}', caminho(id))),
    onSuccess: () => invalidar(),
  })
}

export function useRestaurarDocumento(projetoId: string) {
  const invalidar = useInvalidarDocumentos(projetoId)
  return useMutation({
    mutationFn: (id: string) =>
      exigir(
        client.POST('/api/lixeira/{tipo}/{item_id}/restaurar', {
          params: { path: { tipo: 'documento', item_id: id } },
        }),
      ),
    onSuccess: () => invalidar(),
  })
}

let ultimoEnvio = 0

export type Envio = {
  id: string
  nome: string
  /** 0 a 1. */
  progresso: number
  erro?: string
}

/**
 * Envios em andamento (01 §4.4: barra de progresso por arquivo). Cada arquivo vai sozinho:
 * um acima do limite falha só ele (a linha mostra o erro) e os outros são gravados.
 */
export function useEnvios(projetoId: string) {
  const invalidar = useInvalidarDocumentos(projetoId)
  const [envios, setEnvios] = useState<Envio[]>([])

  const alterar = (id: string, mudanca: Partial<Envio>) =>
    setEnvios((atuais) => atuais.map((e) => (e.id === id ? { ...e, ...mudanca } : e)))
  const dispensar = (id: string) => setEnvios((atuais) => atuais.filter((e) => e.id !== id))

  function enviar(arquivos: Iterable<File>) {
    for (const arquivo of arquivos) {
      ultimoEnvio += 1
      const id = `envio-${ultimoEnvio}`
      setEnvios((atuais) => [...atuais, { id, nome: arquivo.name, progresso: 0 }])
      enviarArquivo(projetoId, arquivo, (progresso) => alterar(id, { progresso }))
        .then(async () => {
          await invalidar()
          dispensar(id)
        })
        .catch((erro: unknown) => alterar(id, { erro: mensagemDoErro(erro) }))
    }
  }

  return { envios, enviar, dispensar }
}
