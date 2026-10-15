import { z } from 'zod'
import type { components } from '@/api/schema'
import { LISTA_STATUS, type StatusProjeto } from '@/features/projetos/status'
import { LISTA_CORES_PROJETO, type CorProjeto } from '@/lib/cores'

// RN-10, RN-11, RN-16. A API valida de novo; aqui é para o erro aparecer antes de enviar.
export const esquemaProjeto = z
  .object({
    nome: z
      .string()
      .trim()
      .min(1, 'Informe o nome do projeto.')
      .max(100, 'Use no máximo 100 caracteres.'),
    descricao: z.string().max(2000, 'Use no máximo 2000 caracteres.'),
    status: z.enum(LISTA_STATUS as [StatusProjeto, ...StatusProjeto[]]),
    cor: z.enum(LISTA_CORES_PROJETO as [CorProjeto, ...CorProjeto[]]),
    data_inicio: z.string().nullable(),
    prazo: z.string().nullable(),
    acompanhar_progresso: z.boolean(),
  })
  .refine((v) => !v.data_inicio || !v.prazo || v.data_inicio <= v.prazo, {
    message: 'O prazo não pode ser anterior ao início.',
    path: ['prazo'],
  })

export type ValoresProjeto = z.output<typeof esquemaProjeto>

export const PROJETO_VAZIO: ValoresProjeto = {
  nome: '',
  descricao: '',
  status: 'em_andamento',
  cor: 'azul',
  data_inicio: null,
  prazo: null,
  acompanhar_progresso: false,
}

export function valoresDoProjeto(projeto: components['schemas']['Projeto']): ValoresProjeto {
  const { nome, descricao, status, cor, data_inicio, prazo, acompanhar_progresso } = projeto
  return { nome, descricao, status, cor, data_inicio, prazo, acompanhar_progresso }
}
