import type { components } from '@/api/schema'
import { isoParaDataLocal } from '@/lib/datas'

export type Recorrencia = components['schemas']['Recorrencia']
export type Unidade = 'dias' | 'semanas' | 'meses' | 'anos'

/** O que o `EditorRecorrencia` controla (01 §4.6); vira o JSON de RN-30 com a primeira data. */
export type EstadoEditor = {
  intervalo: number
  unidade: Unidade
  /** 0 = segunda … 6 = domingo (RN-30). */
  diasSemana: number[]
  diaMes: number | null
}

export const NOMES_DIAS = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
export const LETRAS_DIAS = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D']

const FREQUENCIA: Record<Unidade, Recorrencia['frequencia']> = {
  dias: 'diaria',
  semanas: 'semanal',
  meses: 'mensal',
  anos: 'anual',
}
const UNIDADE: Record<Recorrencia['frequencia'], Unidade> = {
  diaria: 'dias',
  semanal: 'semanas',
  mensal: 'meses',
  anual: 'anos',
}

/** Dia da semana de "AAAA-MM-DD" no padrão de RN-30 (0 = segunda). */
export function diaDaSemana(iso: string): number {
  return (isoParaDataLocal(iso).getDay() + 6) % 7
}

function diaEMes(iso: string): { dia: number; mes: number } {
  const data = isoParaDataLocal(iso)
  return { dia: data.getDate(), mes: data.getMonth() + 1 }
}

export const ESTADO_INICIAL: EstadoEditor = {
  intervalo: 1,
  unidade: 'dias',
  diasSemana: [],
  diaMes: null,
}

export function estadoDaRegra(regra: Recorrencia): EstadoEditor {
  return {
    intervalo: regra.intervalo ?? 1,
    unidade: UNIDADE[regra.frequencia],
    diasSemana: regra.dias_semana ?? [],
    diaMes: regra.frequencia === 'mensal' ? (regra.dia_mes ?? null) : null,
  }
}

/** Ao trocar a unidade, pré-preenche a partir da primeira data (RN-30): o dia da semana e o dia do mês. */
export function trocarUnidade(
  estado: EstadoEditor,
  unidade: Unidade,
  primeiraData: string | null,
): EstadoEditor {
  const novo = { ...estado, unidade }
  if (unidade === 'semanas' && novo.diasSemana.length === 0 && primeiraData) {
    novo.diasSemana = [diaDaSemana(primeiraData)]
  }
  if (unidade === 'meses' && novo.diaMes === null && primeiraData) {
    novo.diaMes = diaEMes(primeiraData).dia
  }
  return novo
}

/** O que falta para a regra ficar válida, na ordem de RN-30; `undefined` se está completa. */
export function erroDoEditor(estado: EstadoEditor, primeiraData: string | null) {
  if (!Number.isInteger(estado.intervalo) || estado.intervalo < 1 || estado.intervalo > 365) {
    return 'Use um intervalo de 1 a 365.'
  }
  if (estado.unidade === 'semanas' && estado.diasSemana.length === 0) {
    return 'Escolha pelo menos um dia da semana.'
  }
  if (
    estado.unidade === 'meses' &&
    (estado.diaMes === null || estado.diaMes < 1 || estado.diaMes > 31)
  ) {
    return 'Informe o dia do mês (1 a 31).'
  }
  if (estado.unidade === 'anos' && !primeiraData) {
    return 'Informe a primeira data: o dia e o mês vêm dela.'
  }
  return undefined
}

/** JSON de RN-30 (campos que não se aplicam = null); `null` se o editor está incompleto. */
export function regraDoEditor(
  estado: EstadoEditor,
  primeiraData: string | null,
): Recorrencia | null {
  if (erroDoEditor(estado, primeiraData)) return null
  const base = {
    frequencia: FREQUENCIA[estado.unidade],
    intervalo: estado.intervalo,
    dias_semana: null,
    dia_mes: null,
    mes: null,
  }
  switch (estado.unidade) {
    case 'semanas':
      return { ...base, dias_semana: [...new Set(estado.diasSemana)].sort((a, b) => a - b) }
    case 'meses':
      return { ...base, dia_mes: estado.diaMes }
    case 'anos': {
      const { dia, mes } = diaEMes(primeiraData!)
      return { ...base, dia_mes: dia, mes }
    }
    default:
      return base
  }
}

function lista(itens: string[]) {
  return itens.length === 1 ? itens[0] : `${itens.slice(0, -1).join(', ')} e ${itens.at(-1)}`
}

/**
 * Pré-visualização com os textos de RN-35 (05 §8). O texto oficial vem da API depois de salvar
 * (`recorrencia_descricao`), calculado por `app/domain/recorrencia.py`.
 */
export function descreverRecorrencia(regra: Recorrencia): string {
  const n = regra.intervalo ?? 1
  if (regra.frequencia === 'diaria') return n === 1 ? 'todo dia' : `a cada ${n} dias`
  if (regra.frequencia === 'semanal') {
    const dias = regra.dias_semana ?? []
    const nomes = lista(dias.map((dia) => NOMES_DIAS[dia] ?? ''))
    if (n > 1) return `a cada ${n} semanas: ${nomes}`
    if (dias.join() === '0,1,2,3,4,5,6') return 'todo dia'
    if (dias.join() === '0,1,2,3,4') return 'de segunda a sexta'
    if (dias.length === 1) return `${(dias[0] ?? 0) < 5 ? 'toda' : 'todo'} ${nomes}`
    return `toda semana: ${nomes}`
  }
  const dia = regra.dia_mes ?? 1
  if (regra.frequencia === 'mensal') {
    const fim = dia >= 29 ? ' (ou o último dia do mês)' : ''
    return n === 1 ? `todo dia ${dia}${fim}` : `a cada ${n} meses, no dia ${dia}${fim}`
  }
  const data = `${String(dia).padStart(2, '0')}/${String(regra.mes ?? 1).padStart(2, '0')}`
  return n === 1 ? `todo ano em ${data}` : `a cada ${n} anos em ${data}`
}
