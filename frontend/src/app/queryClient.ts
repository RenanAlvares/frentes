import { QueryClient } from '@tanstack/react-query'
import { ErroApi } from '@/api/erros'

/** 05 §4: queries tentam de novo 1 vez; erro 4xx da API (ex.: 404) não muda ao repetir. */
export function tentarDeNovo(falhas: number, erro: unknown): boolean {
  if (erro instanceof ErroApi && erro.status < 500) return false
  return falhas < 1
}

export function criarQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, refetchOnWindowFocus: true, retry: tentarDeNovo },
      mutations: { retry: 0 },
    },
  })
}
