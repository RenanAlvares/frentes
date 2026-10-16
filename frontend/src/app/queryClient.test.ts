import { describe, expect, it } from 'vitest'
import { criarErroApi } from '@/api/erros'
import { criarQueryClient, tentarDeNovo } from '@/app/queryClient'

describe('criarQueryClient', () => {
  it('usa os padrões de 05-frontend §4', () => {
    const { queries, mutations } = criarQueryClient().getDefaultOptions()

    expect(queries).toMatchObject({ staleTime: 30_000, refetchOnWindowFocus: true })
    expect(queries?.retry).toBe(tentarDeNovo)
    expect(mutations).toMatchObject({ retry: 0 })
  })

  it('tenta de novo 1 vez em falha de rede ou 5xx, nunca em 4xx', () => {
    expect(tentarDeNovo(0, new TypeError('Failed to fetch'))).toBe(true)
    expect(tentarDeNovo(0, criarErroApi(502, 'Bad Gateway'))).toBe(true)
    expect(tentarDeNovo(1, criarErroApi(500, undefined))).toBe(false)
    expect(tentarDeNovo(0, criarErroApi(404, undefined))).toBe(false)
  })
})
