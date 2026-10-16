import type { components } from '@/api/schema'

export type Tarefa = components['schemas']['Tarefa']
export type Quadro = components['schemas']['Quadro']
export type StatusTarefa = components['schemas']['StatusTarefa']

/** Ids das tarefas de cada coluna, na ordem exibida. */
export type Colunas = Record<StatusTarefa, string[]>

export const COLUNAS: readonly StatusTarefa[] = ['pendente', 'em_andamento', 'concluida']

export const ROTULO_COLUNA: Record<StatusTarefa, string> = {
  pendente: 'Pendente',
  em_andamento: 'Em andamento',
  concluida: 'Concluída',
}

export function colunasDoQuadro(quadro: Quadro): Colunas {
  return {
    pendente: quadro.pendente.map((t) => t.id),
    em_andamento: quadro.em_andamento.map((t) => t.id),
    concluida: quadro.concluida.map((t) => t.id),
  }
}

function ehColuna(id: string): id is StatusTarefa {
  return (COLUNAS as readonly string[]).includes(id)
}

/** Coluna de uma tarefa, ou a própria coluna quando o id é de uma coluna (área vazia). */
export function colunaDe(colunas: Colunas, id: string): StatusTarefa | undefined {
  if (ehColuna(id)) return id
  return COLUNAS.find((coluna) => colunas[coluna].includes(id))
}

/**
 * Põe `ativo` junto de `sobre` (uma tarefa, antes ou `depois` dela, ou uma coluna: no fim).
 * Concluída é ordenada pela API por `concluida_em` (RN-25): quem entra vai para o topo e
 * reordenar dentro dela não muda nada.
 */
export function reposicionar(
  colunas: Colunas,
  ativo: string,
  sobre: string,
  depois: boolean,
): Colunas {
  const origem = colunaDe(colunas, ativo)
  const destino = colunaDe(colunas, sobre)
  if (!origem || !destino || ativo === sobre) return colunas
  if (destino === 'concluida' && origem === 'concluida') return colunas

  const semAtivo = { ...colunas, [origem]: colunas[origem].filter((id) => id !== ativo) }
  const alvo = semAtivo[destino]
  let indice: number
  if (destino === 'concluida') indice = 0
  else if (ehColuna(sobre)) indice = alvo.length
  else indice = alvo.indexOf(sobre) + (depois ? 1 : 0)
  return { ...semAtivo, [destino]: [...alvo.slice(0, indice), ativo, ...alvo.slice(indice)] }
}

/** Pedido de RN-25 para a posição atual de `ativo`: coluna e índice nela. */
export function pedidoDeMover(colunas: Colunas, ativo: string) {
  const status = colunaDe(colunas, ativo)
  return status ? { status, indice: colunas[status].indexOf(ativo) } : undefined
}

/** O quadro como ficará depois do movimento (atualização otimista, 05 §4). */
export function aplicarNoQuadro(quadro: Quadro, colunas: Colunas, ativo: string): Quadro {
  const porId = new Map(
    [...quadro.pendente, ...quadro.em_andamento, ...quadro.concluida].map((t) => [t.id, t]),
  )
  const montar = (status: StatusTarefa) =>
    colunas[status].flatMap((id, posicao) => {
      const tarefa = porId.get(id)
      if (!tarefa) return []
      return [id === ativo ? { ...tarefa, status, posicao } : { ...tarefa, posicao }]
    })
  const antes = quadro.concluida.some((t) => t.id === ativo)
  const agora = colunas.concluida.includes(ativo)
  return {
    pendente: montar('pendente'),
    em_andamento: montar('em_andamento'),
    concluida: montar('concluida'),
    total_concluidas: quadro.total_concluidas + (agora ? 1 : 0) - (antes ? 1 : 0),
  }
}
