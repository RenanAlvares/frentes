import { describe, expect, it } from 'vitest'
import { formatarData } from '@/lib/datas'

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
