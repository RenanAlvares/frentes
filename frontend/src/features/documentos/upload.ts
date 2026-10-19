import { criarErroApi } from '@/api/erros'
import type { components } from '@/api/schema'

export type Documento = components['schemas']['Documento']

/** Rota do arquivo (RN-71: a API decide `inline` ou `attachment`). */
export const urlDoArquivo = (documentoId: string) =>
  `/api/documentos/${encodeURIComponent(documentoId)}/arquivo`

/**
 * Envia um arquivo (roadmap 4.2: uma requisição por arquivo, com progresso próprio).
 * `XMLHttpRequest` e não o client tipado: `fetch` não informa o progresso do envio.
 */
export function enviarArquivo(
  projetoId: string,
  arquivo: File,
  onProgresso: (fracao: number) => void,
): Promise<Documento[]> {
  return new Promise((resolver, rejeitar) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `/api/projetos/${encodeURIComponent(projetoId)}/documentos`)
    xhr.responseType = 'json'
    xhr.upload.onprogress = (evento) => {
      if (evento.lengthComputable && evento.total > 0) onProgresso(evento.loaded / evento.total)
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolver(xhr.response as Documento[])
      else rejeitar(criarErroApi(xhr.status, xhr.response))
    }
    // Falha de rede: vira a mensagem genérica (`mensagemDoErro`).
    xhr.onerror = () => rejeitar(new Error('Falha de rede no envio'))
    const corpo = new FormData()
    corpo.append('arquivos', arquivo)
    xhr.send(corpo)
  })
}
