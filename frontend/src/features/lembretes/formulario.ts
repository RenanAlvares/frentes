import { z } from 'zod'
import type { components } from '@/api/schema'
import {
  esquemaEditor,
  ESTADO_INICIAL,
  erroDoEditor,
  estadoDaRegra,
  regraDoEditor,
} from '@/lib/recorrencia'

export type Lembrete = components['schemas']['Lembrete']

// RN-40. A API valida de novo; aqui é para o erro aparecer antes de enviar.
export const esquemaLembrete = z
  .object({
    titulo: z
      .string()
      .trim()
      .min(1, 'Informe o título do lembrete.')
      .max(200, 'Use no máximo 200 caracteres.'),
    observacao: z.string().max(2000, 'Use no máximo 2000 caracteres.'),
    vencimento: z.string().nullable(),
    /** Vazio: na criação, o padrão das configurações (RN-40); na edição, não muda. */
    antecedencia_dias: z.number().nullable(),
    repetir: z.boolean(),
    editor: esquemaEditor,
  })
  .superRefine((valores, contexto) => {
    const erro = (path: string, message: string) =>
      contexto.addIssue({ code: 'custom', path: [path], message })
    if (!valores.vencimento) erro('vencimento', 'Informe o vencimento.')
    const dias = valores.antecedencia_dias
    if (dias !== null && (!Number.isInteger(dias) || dias < 0 || dias > 60)) {
      erro('antecedencia_dias', 'Use de 0 a 60 dias.')
    }
    const doEditor = erroDoEditor(valores.editor, valores.vencimento)
    if (valores.repetir && valores.vencimento && doEditor) erro('editor', doEditor)
  })

export type ValoresLembrete = z.output<typeof esquemaLembrete>
export type SujosLembrete = Partial<Record<keyof ValoresLembrete, unknown>>

export const LEMBRETE_VAZIO: ValoresLembrete = {
  titulo: '',
  observacao: '',
  vencimento: null,
  antecedencia_dias: null,
  repetir: false,
  editor: ESTADO_INICIAL,
}

export function valoresDoLembrete(lembrete: Lembrete): ValoresLembrete {
  const { titulo, observacao, vencimento, antecedencia_dias, recorrencia } = lembrete
  return {
    titulo,
    observacao,
    vencimento,
    antecedencia_dias,
    repetir: recorrencia !== null,
    editor: recorrencia ? estadoDaRegra(recorrencia) : ESTADO_INICIAL,
  }
}

/** A regra de RN-30 (a primeira data é o vencimento) ou `null` sem "Repetir". */
const recorrencia = (valores: ValoresLembrete) =>
  valores.repetir ? regraDoEditor(valores.editor, valores.vencimento) : null

export function corpoCriarLembrete(valores: ValoresLembrete) {
  const { titulo, observacao, antecedencia_dias } = valores
  return {
    titulo,
    observacao,
    vencimento: valores.vencimento ?? '',
    ...(antecedencia_dias === null ? {} : { antecedencia_dias }),
    recorrencia: recorrencia(valores),
  }
}

/** PATCH: só o que mudou; `recorrencia: null` remove a repetição. */
export function corpoAtualizarLembrete(valores: ValoresLembrete, sujos: SujosLembrete) {
  const corpo: Partial<ReturnType<typeof corpoCriarLembrete>> = {}
  if (sujos.titulo) corpo.titulo = valores.titulo
  if (sujos.observacao) corpo.observacao = valores.observacao
  if (sujos.vencimento && valores.vencimento) corpo.vencimento = valores.vencimento
  if (sujos.antecedencia_dias && valores.antecedencia_dias !== null) {
    corpo.antecedencia_dias = valores.antecedencia_dias
  }
  // A regra anual vem do vencimento: mudar a data também refaz a regra.
  if (sujos.repetir || sujos.editor || (sujos.vencimento && valores.repetir)) {
    corpo.recorrencia = recorrencia(valores)
  }
  return corpo
}
