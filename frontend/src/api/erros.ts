import type { components } from '@/api/schema'

type ErroDetalhe = components['schemas']['ErroDetalhe']

// 01-produto §5: erro genérico.
export const MENSAGEM_GENERICA = 'Não foi possível concluir a ação. Tente de novo.'

/** Erro devolvido pela API no formato de 04-api (Formato de erro). */
export class ErroApi extends Error {
  readonly status: number
  readonly codigo: string
  readonly campos: Record<string, string>

  constructor(status: number, detalhe: ErroDetalhe) {
    super(detalhe.mensagem)
    this.name = 'ErroApi'
    this.status = status
    this.codigo = detalhe.codigo
    this.campos = detalhe.campos ?? {}
  }
}

function ehTexto(valor: unknown): valor is string {
  return typeof valor === 'string'
}

function ehErroDetalhe(valor: unknown): valor is ErroDetalhe {
  if (typeof valor !== 'object' || valor === null) return false
  const { codigo, mensagem, campos } = valor as Record<string, unknown>
  const camposValidos =
    campos === undefined ||
    campos === null ||
    (typeof campos === 'object' && Object.values(campos).every(ehTexto))
  return ehTexto(codigo) && ehTexto(mensagem) && camposValidos
}

/** Converte o corpo de uma resposta de erro; corpo fora do padrão (ex.: proxy) vira erro genérico. */
export function criarErroApi(status: number, corpo: unknown): ErroApi {
  const detalhe =
    typeof corpo === 'object' && corpo !== null && 'erro' in corpo ? corpo.erro : undefined
  if (ehErroDetalhe(detalhe)) {
    return new ErroApi(status, detalhe)
  }
  const codigo = status >= 500 ? 'erro_interno' : 'requisicao_invalida'
  return new ErroApi(status, { codigo, mensagem: MENSAGEM_GENERICA })
}

/** Mensagem para o toast: a da API ou a genérica (falha de rede, erro inesperado). */
export function mensagemDoErro(erro: unknown): string {
  return erro instanceof ErroApi ? erro.message : MENSAGEM_GENERICA
}

/** Campo → mensagem dos erros de validação (422), para `setError` nos formulários. */
export function camposDoErro(erro: unknown): Record<string, string> {
  return erro instanceof ErroApi ? erro.campos : {}
}
