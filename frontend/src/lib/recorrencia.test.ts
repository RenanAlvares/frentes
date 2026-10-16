import { describe, expect, it } from 'vitest'
import {
  descreverRecorrencia,
  diaDaSemana,
  ESTADO_INICIAL,
  erroDoEditor,
  estadoDaRegra,
  regraDoEditor,
  trocarUnidade,
  type EstadoEditor,
  type Recorrencia,
} from '@/lib/recorrencia'

const regra = (dados: Partial<Recorrencia> & Pick<Recorrencia, 'frequencia'>): Recorrencia => ({
  intervalo: 1,
  dias_semana: null,
  dia_mes: null,
  mes: null,
  ...dados,
})

const estado = (dados: Partial<EstadoEditor>): EstadoEditor => ({ ...ESTADO_INICIAL, ...dados })

// 14/10/2026 é quarta.
const QUARTA = '2026-10-14'

describe('regraDoEditor: editor → JSON de RN-30', () => {
  it.each([
    [estado({}), regra({ frequencia: 'diaria' })],
    [estado({ intervalo: 7 }), regra({ frequencia: 'diaria', intervalo: 7 })],
    [
      estado({ unidade: 'semanas', diasSemana: [4, 0, 2, 0] }),
      regra({ frequencia: 'semanal', dias_semana: [0, 2, 4] }),
    ],
    [
      estado({ unidade: 'semanas', intervalo: 2, diasSemana: [0] }),
      regra({ frequencia: 'semanal', intervalo: 2, dias_semana: [0] }),
    ],
    [estado({ unidade: 'meses', diaMes: 31 }), regra({ frequencia: 'mensal', dia_mes: 31 })],
    // Anual: dia e mês da primeira data, mesmo se o editor tinha outro dia do mês.
    [
      estado({ unidade: 'anos', intervalo: 2, diaMes: 5 }),
      regra({ frequencia: 'anual', intervalo: 2, dia_mes: 14, mes: 10 }),
    ],
  ])('%j', (entrada, esperado) => {
    expect(regraDoEditor(entrada, QUARTA)).toEqual(esperado)
  })

  it.each([
    [estado({ unidade: 'semanas' }), QUARTA, 'Escolha pelo menos um dia da semana.'],
    [estado({ unidade: 'meses' }), QUARTA, 'Informe o dia do mês (1 a 31).'],
    [estado({ unidade: 'meses', diaMes: 32 }), QUARTA, 'Informe o dia do mês (1 a 31).'],
    [estado({ unidade: 'anos' }), null, 'Informe a primeira data: o dia e o mês vêm dela.'],
    [estado({ intervalo: 0 }), QUARTA, 'Use um intervalo de 1 a 365.'],
    [estado({ intervalo: 366 }), QUARTA, 'Use um intervalo de 1 a 365.'],
  ])('incompleto: %j com %s', (entrada, primeiraData, erro) => {
    expect(erroDoEditor(entrada, primeiraData)).toBe(erro)
    expect(regraDoEditor(entrada, primeiraData)).toBeNull()
  })
})

describe('trocarUnidade: pré-preenche pela primeira data', () => {
  it('semanas marca o dia da semana da primeira data', () => {
    expect(trocarUnidade(ESTADO_INICIAL, 'semanas', QUARTA).diasSemana).toEqual([2])
    expect(trocarUnidade(ESTADO_INICIAL, 'semanas', null).diasSemana).toEqual([])
  })

  it('meses usa o dia da primeira data; não troca o que o usuário já escolheu', () => {
    expect(trocarUnidade(ESTADO_INICIAL, 'meses', QUARTA).diaMes).toBe(14)
    expect(trocarUnidade(estado({ diaMes: 5 }), 'meses', QUARTA).diaMes).toBe(5)
    expect(trocarUnidade(estado({ diasSemana: [4] }), 'semanas', QUARTA).diasSemana).toEqual([4])
  })

  it('dia da semana nunca desloca (0 = segunda, 6 = domingo)', () => {
    expect(diaDaSemana('2026-10-12')).toBe(0)
    expect(diaDaSemana('2026-10-18')).toBe(6)
    expect(diaDaSemana('2028-02-29')).toBe(1)
  })
})

describe('estadoDaRegra: regra salva → editor', () => {
  it('ida e volta', () => {
    const regras = [
      regra({ frequencia: 'diaria', intervalo: 3 }),
      regra({ frequencia: 'semanal', dias_semana: [1, 3] }),
      regra({ frequencia: 'mensal', intervalo: 2, dia_mes: 10 }),
    ]
    for (const original of regras) {
      expect(regraDoEditor(estadoDaRegra(original), QUARTA)).toEqual(original)
    }
  })
})

describe('descreverRecorrencia: textos de RN-35', () => {
  it.each([
    [regra({ frequencia: 'diaria' }), 'todo dia'],
    [regra({ frequencia: 'diaria', intervalo: 7 }), 'a cada 7 dias'],
    [regra({ frequencia: 'semanal', dias_semana: [0] }), 'toda segunda'],
    [regra({ frequencia: 'semanal', dias_semana: [5] }), 'todo sábado'],
    [
      regra({ frequencia: 'semanal', dias_semana: [0, 2, 4] }),
      'toda semana: segunda, quarta e sexta',
    ],
    [regra({ frequencia: 'semanal', dias_semana: [0, 1, 2, 3, 4] }), 'de segunda a sexta'],
    [regra({ frequencia: 'semanal', dias_semana: [0, 1, 2, 3, 4, 5, 6] }), 'todo dia'],
    [
      regra({ frequencia: 'semanal', intervalo: 2, dias_semana: [0, 2] }),
      'a cada 2 semanas: segunda e quarta',
    ],
    [regra({ frequencia: 'mensal', dia_mes: 5 }), 'todo dia 5'],
    [regra({ frequencia: 'mensal', intervalo: 3, dia_mes: 10 }), 'a cada 3 meses, no dia 10'],
    [regra({ frequencia: 'mensal', dia_mes: 31 }), 'todo dia 31 (ou o último dia do mês)'],
    [regra({ frequencia: 'mensal', dia_mes: 29 }), 'todo dia 29 (ou o último dia do mês)'],
    [regra({ frequencia: 'anual', dia_mes: 20, mes: 11 }), 'todo ano em 20/11'],
    [regra({ frequencia: 'anual', intervalo: 2, dia_mes: 20, mes: 11 }), 'a cada 2 anos em 20/11'],
  ])('%j → %s', (entrada, texto) => {
    expect(descreverRecorrencia(entrada)).toBe(texto)
  })
})
