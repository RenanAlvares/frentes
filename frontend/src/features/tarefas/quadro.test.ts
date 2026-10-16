import { describe, expect, it } from 'vitest'
import {
  aplicarNoQuadro,
  colunaDe,
  pedidoDeMover,
  reposicionar,
  type Colunas,
  type Quadro,
  type Tarefa,
} from '@/features/tarefas/quadro'

const base: Colunas = { pendente: ['a', 'b', 'c', 'd'], em_andamento: ['x', 'y'], concluida: ['z'] }

describe('reposicionar (RN-25)', () => {
  it.each([
    // Mesma coluna: igual a arrayMove (descendo fica depois do alvo, subindo fica antes).
    ['a', 'c', true, { ...base, pendente: ['b', 'c', 'a', 'd'] }],
    ['d', 'b', false, { ...base, pendente: ['a', 'd', 'b', 'c'] }],
    // Outra coluna: antes ou depois do alvo, ou no fim ao soltar na área da coluna.
    ['a', 'y', false, { ...base, pendente: ['b', 'c', 'd'], em_andamento: ['x', 'a', 'y'] }],
    ['a', 'y', true, { ...base, pendente: ['b', 'c', 'd'], em_andamento: ['x', 'y', 'a'] }],
    ['x', 'pendente', false, { ...base, pendente: ['a', 'b', 'c', 'd', 'x'], em_andamento: ['y'] }],
    // Concluída: quem entra vai para o topo (é a mais recente).
    ['b', 'z', true, { ...base, pendente: ['a', 'c', 'd'], concluida: ['b', 'z'] }],
    ['b', 'concluida', false, { ...base, pendente: ['a', 'c', 'd'], concluida: ['b', 'z'] }],
    // Sair de Concluída.
    ['z', 'x', false, { ...base, em_andamento: ['z', 'x', 'y'], concluida: [] }],
  ] as const)('%s sobre %s (depois=%s)', (ativo, sobre, depois, esperado) => {
    expect(reposicionar(base, ativo, sobre, depois)).toEqual(esperado)
  })

  it('coluna vazia recebe a tarefa', () => {
    const vazia: Colunas = { pendente: ['a'], em_andamento: [], concluida: [] }

    expect(reposicionar(vazia, 'a', 'em_andamento', false)).toEqual({
      pendente: [],
      em_andamento: ['a'],
      concluida: [],
    })
  })

  it('sem efeito: sobre si mesma, dentro de Concluída ou id desconhecido', () => {
    const concluidas: Colunas = { ...base, concluida: ['z', 'w'] }

    expect(reposicionar(base, 'a', 'a', true)).toBe(base)
    expect(reposicionar(concluidas, 'z', 'w', true)).toBe(concluidas)
    expect(reposicionar(base, 'nao-existe', 'a', false)).toBe(base)
  })
})

describe('pedidoDeMover e colunaDe', () => {
  it('devolve a coluna e o índice da tarefa', () => {
    expect(pedidoDeMover(base, 'y')).toEqual({ status: 'em_andamento', indice: 1 })
    expect(pedidoDeMover(base, 'nao-existe')).toBeUndefined()
    expect(colunaDe(base, 'concluida')).toBe('concluida')
  })
})

function tarefa(id: string, status: Tarefa['status']): Tarefa {
  return {
    id,
    projeto_id: 'p',
    titulo: id,
    descricao: '',
    status,
    prioridade: 'media',
    tipo: 'simples',
    prazo: null,
    recorrencia: null,
    recorrencia_descricao: null,
    meta_mensal: null,
    progresso_mes: null,
    posicao: 0,
    concluida_em: null,
    atrasada: false,
    criado_em: '2026-10-14T15:00:00Z',
    atualizado_em: '2026-10-14T15:00:00Z',
  }
}

describe('aplicarNoQuadro (otimista)', () => {
  const quadro: Quadro = {
    pendente: [tarefa('a', 'pendente'), tarefa('b', 'pendente')],
    em_andamento: [],
    concluida: [tarefa('z', 'concluida')],
    total_concluidas: 25,
  }

  it('muda o status da tarefa movida, renumera e ajusta o total de concluídas', () => {
    const colunas: Colunas = { pendente: ['b'], em_andamento: [], concluida: ['a', 'z'] }

    const novo = aplicarNoQuadro(quadro, colunas, 'a')

    expect(novo.pendente.map((t) => [t.id, t.posicao])).toEqual([['b', 0]])
    expect(novo.concluida.map((t) => [t.id, t.status])).toEqual([
      ['a', 'concluida'],
      ['z', 'concluida'],
    ])
    expect(novo.total_concluidas).toBe(26)
  })

  it('tirar de Concluída diminui o total', () => {
    const colunas: Colunas = { pendente: ['a', 'b'], em_andamento: ['z'], concluida: [] }

    const novo = aplicarNoQuadro(quadro, colunas, 'z')

    expect(novo.em_andamento.map((t) => t.status)).toEqual(['em_andamento'])
    expect(novo.total_concluidas).toBe(24)
  })
})
