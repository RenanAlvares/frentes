import { describe, expect, it } from 'vitest'
import {
  anoDe,
  antesDe,
  dataLocalParaIso,
  formatarData,
  formatarDataCurta,
  isoParaDataLocal,
  paraIso,
} from '@/lib/datas'

describe('formatarData', () => {
  it.each([
    ['2026-10-16', '16/10/2026'],
    // Viradas de mês e ano: nunca desloca o dia (sem conversão de fuso).
    ['2026-01-01', '01/01/2026'],
    ['2026-12-31', '31/12/2026'],
    ['2028-02-29', '29/02/2028'],
  ])('%s → %s', (iso, esperado) => {
    expect(formatarData(iso)).toBe(esperado)
  })

  it.each(['16/10/2026', '2026-10-16T00:00:00Z', ''])('rejeita %j', (valor) => {
    expect(() => formatarData(valor)).toThrow('AAAA-MM-DD')
  })
})

describe('formatarDataCurta (01 §5, cards)', () => {
  it('omite o ano quando é o atual', () => {
    expect(formatarDataCurta('2026-11-30', 2026)).toBe('30/11')
    expect(formatarDataCurta('2027-01-05', 2026)).toBe('05/01/2027')
  })
})

describe('paraIso e conversão com o calendário', () => {
  it('monta AAAA-MM-DD com zeros à esquerda', () => {
    expect(paraIso(5, 1, 2027)).toBe('2027-01-05')
    expect(paraIso(31, 12, 2026)).toBe('2026-12-31')
  })

  it.each(['2026-01-01', '2026-02-28', '2028-02-29', '2026-10-18', '2026-12-31'])(
    'ida e volta sem deslocar o dia: %s',
    (iso) => {
      const data = isoParaDataLocal(iso)
      expect(data.getHours()).toBe(0)
      expect(dataLocalParaIso(data)).toBe(iso)
    },
  )

  it('usa os getters locais, não o UTC', () => {
    // 23h do dia 31 no horário local continua sendo dia 31.
    expect(dataLocalParaIso(new Date(2026, 11, 31, 23, 30))).toBe('2026-12-31')
  })
})

describe('anoDe e antesDe', () => {
  it('lê o ano e compara datas pela ordem do texto', () => {
    expect(anoDe('2026-10-14')).toBe(2026)
    expect(antesDe('2026-10-13', '2026-10-14')).toBe(true)
    expect(antesDe('2026-10-14', '2026-10-14')).toBe(false)
    expect(antesDe('2027-01-01', '2026-12-31')).toBe(false)
  })

  it('rejeita data fora do formato', () => {
    expect(() => antesDe('14/10/2026', '2026-10-14')).toThrow('AAAA-MM-DD')
  })
})
