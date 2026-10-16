import { z } from 'zod'
import type { components } from '@/api/schema'
import type { StatusTarefa, Tarefa } from '@/features/tarefas/quadro'

type Prioridade = components['schemas']['Prioridade']

// 01 §5.
export const ROTULO_PRIORIDADE: Record<Prioridade, string> = {
  baixa: 'Baixa',
  media: 'Média',
  alta: 'Alta',
}
export const LISTA_PRIORIDADES = Object.keys(ROTULO_PRIORIDADE) as Prioridade[]

export const ROTULO_TIPO: Record<Tarefa['tipo'], string> = {
  simples: 'Simples',
  repetida: 'Repetida',
  meta_mensal: 'Meta mensal',
}

// RN-20. A API valida de novo; aqui é para o erro aparecer antes de enviar.
export const esquemaTarefa = z.object({
  titulo: z
    .string()
    .trim()
    .min(1, 'Informe o título da tarefa.')
    .max(200, 'Use no máximo 200 caracteres.'),
  descricao: z.string().max(5000, 'Use no máximo 5000 caracteres.'),
  status: z.enum(['pendente', 'em_andamento', 'concluida'] satisfies StatusTarefa[]),
  prioridade: z.enum(LISTA_PRIORIDADES as [Prioridade, ...Prioridade[]]),
  prazo: z.string().nullable(),
})

export type ValoresTarefa = z.output<typeof esquemaTarefa>

// Criação: tarefa simples em Pendente, prioridade média (RN-20, RN-25).
export const TAREFA_VAZIA: ValoresTarefa = {
  titulo: '',
  descricao: '',
  status: 'pendente',
  prioridade: 'media',
  prazo: null,
}

export function valoresDaTarefa(tarefa: Tarefa): ValoresTarefa {
  const { titulo, descricao, status, prioridade, prazo } = tarefa
  return { titulo, descricao, status, prioridade, prazo }
}
