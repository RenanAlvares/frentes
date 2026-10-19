import { z } from 'zod'
import type { components } from '@/api/schema'
import type { CorAnotacao } from '@/lib/cores'

export type Anotacao = components['schemas']['Anotacao']

// RN-80. A API valida de novo; aqui é para o erro aparecer antes de enviar.
export const esquemaAnotacao = z.object({
  titulo: z.string().trim().max(120, 'Use no máximo 120 caracteres.'),
  texto: z
    .string()
    .trim()
    .min(1, 'Escreva o texto da anotação.')
    .max(10000, 'Use no máximo 10000 caracteres.'),
  cor: z.custom<CorAnotacao>(),
  fixada: z.boolean(),
})

export type ValoresAnotacao = z.output<typeof esquemaAnotacao>
export type SujosAnotacao = Partial<Record<keyof ValoresAnotacao, unknown>>

export const ANOTACAO_VAZIA: ValoresAnotacao = {
  titulo: '',
  texto: '',
  cor: 'amarelo',
  fixada: false,
}

export function valoresDaAnotacao({ titulo, texto, cor, fixada }: Anotacao): ValoresAnotacao {
  return { titulo, texto, cor, fixada }
}

/** PATCH: só o que mudou. */
export function corpoAtualizarAnotacao(valores: ValoresAnotacao, sujos: SujosAnotacao) {
  const campos = Object.keys(valores) as (keyof ValoresAnotacao)[]
  return Object.fromEntries(
    campos.filter((campo) => sujos[campo]).map((campo) => [campo, valores[campo]]),
  ) as Partial<ValoresAnotacao>
}
