import { describe, expect, it } from 'vitest'
import { criarQueryClient } from '@/app/queryClient'

describe('criarQueryClient', () => {
  it('usa os padrões de 05-frontend §4', () => {
    const { queries, mutations } = criarQueryClient().getDefaultOptions()

    expect(queries).toMatchObject({ staleTime: 30_000, refetchOnWindowFocus: true, retry: 1 })
    expect(mutations).toMatchObject({ retry: 0 })
  })
})
