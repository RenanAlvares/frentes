import { z } from 'zod'
import type { components } from '@/api/schema'
import type { StatusTarefa, Tarefa } from '@/features/tarefas/quadro'
import {
  ESTADO_INICIAL,
  erroDoEditor,
  estadoDaRegra,
  regraDoEditor,
  type Recorrencia,
} from '@/lib/recorrencia'

type Prioridade = components['schemas']['Prioridade']
type Tipo = Tarefa['tipo']

// 01 §5.
export const ROTULO_PRIORIDADE: Record<Prioridade, string> = {
  baixa: 'Baixa',
  media: 'Média',
  alta: 'Alta',
}
export const LISTA_PRIORIDADES = Object.keys(ROTULO_PRIORIDADE) as Prioridade[]

export const ROTULO_TIPO: Record<Tipo, string> = {
  simples: 'Simples',
  repetida: 'Repetida',
  meta_mensal: 'Meta mensal',
}
export const LISTA_TIPOS = Object.keys(ROTULO_TIPO) as Tipo[]

const estadoEditor = z.object({
  intervalo: z.number(),
  unidade: z.enum(['dias', 'semanas', 'meses', 'anos']),
  diasSemana: z.array(z.number()),
  diaMes: z.number().nullable(),
})

// RN-20 e RN-21 por tipo. A API valida de novo; aqui é para o erro aparecer antes de enviar.
export const esquemaTarefa = z
  .object({
    titulo: z
      .string()
      .trim()
      .min(1, 'Informe o título da tarefa.')
      .max(200, 'Use no máximo 200 caracteres.'),
    descricao: z.string().max(5000, 'Use no máximo 5000 caracteres.'),
    status: z.enum(['pendente', 'em_andamento', 'concluida'] satisfies StatusTarefa[]),
    prioridade: z.enum(LISTA_PRIORIDADES as [Prioridade, ...Prioridade[]]),
    tipo: z.enum(LISTA_TIPOS as [Tipo, ...Tipo[]]),
    prazo: z.string().nullable(),
    editor: estadoEditor,
    meta_mensal: z.number().nullable(),
  })
  .superRefine((valores, contexto) => {
    const erro = (path: string, message: string) =>
      contexto.addIssue({ code: 'custom', path: [path], message })
    if (valores.tipo === 'repetida') {
      if (!valores.prazo) erro('prazo', 'Informe a primeira data.')
      const doEditor = erroDoEditor(valores.editor, valores.prazo)
      // Sem a primeira data, o erro já aparece no campo da data.
      if (doEditor && valores.prazo) erro('editor', doEditor)
    }
    const meta = valores.meta_mensal
    if (
      valores.tipo === 'meta_mensal' &&
      (meta === null || !Number.isInteger(meta) || meta < 1 || meta > 31)
    ) {
      erro('meta_mensal', 'Informe quantas vezes por mês (1 a 31).')
    }
  })

export type ValoresTarefa = z.output<typeof esquemaTarefa>
/** Campos alterados no formulário (`dirtyFields` do react-hook-form). */
export type Sujos = Partial<Record<keyof ValoresTarefa, unknown>>

// Criação: tarefa simples em Pendente, prioridade média (RN-20, RN-25).
export const TAREFA_VAZIA: ValoresTarefa = {
  titulo: '',
  descricao: '',
  status: 'pendente',
  prioridade: 'media',
  tipo: 'simples',
  prazo: null,
  editor: ESTADO_INICIAL,
  meta_mensal: null,
}

export function valoresDaTarefa(tarefa: Tarefa): ValoresTarefa {
  const { titulo, descricao, status, prioridade, tipo, prazo, meta_mensal } = tarefa
  const editor = tarefa.recorrencia ? estadoDaRegra(tarefa.recorrencia) : ESTADO_INICIAL
  return { titulo, descricao, status, prioridade, tipo, prazo, editor, meta_mensal }
}

/** RN-21: só os campos do tipo; os que não se aplicam vão `null` (a API valida o estado final). */
function camposDoTipo(valores: ValoresTarefa) {
  const recorrencia: Recorrencia | null =
    valores.tipo === 'repetida' ? regraDoEditor(valores.editor, valores.prazo) : null
  return {
    tipo: valores.tipo,
    prazo: valores.tipo === 'meta_mensal' ? null : valores.prazo,
    recorrencia,
    meta_mensal: valores.tipo === 'meta_mensal' ? valores.meta_mensal : null,
  }
}

export function corpoCriar(valores: ValoresTarefa) {
  const { titulo, descricao, prioridade } = valores
  return { titulo, descricao, prioridade, ...camposDoTipo(valores) }
}

/** PATCH: o que mudou; mexer no tipo, prazo, regra ou meta manda os campos do tipo juntos. */
export function corpoAtualizar(valores: ValoresTarefa, sujos: Sujos) {
  const corpo: Partial<ReturnType<typeof corpoCriar> & { status: StatusTarefa }> = {}
  if (sujos.titulo) corpo.titulo = valores.titulo
  if (sujos.descricao) corpo.descricao = valores.descricao
  if (sujos.prioridade) corpo.prioridade = valores.prioridade
  // RN-24: a coluna de uma meta vem das execuções; status não se edita.
  if (sujos.status && valores.tipo !== 'meta_mensal') corpo.status = valores.status
  if (sujos.tipo || sujos.prazo || sujos.editor || sujos.meta_mensal) {
    Object.assign(corpo, camposDoTipo(valores))
  }
  return corpo
}
