import { QueryClient } from '@tanstack/react-query'

// 05-frontend §4.
export function criarQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, refetchOnWindowFocus: true, retry: 1 },
      mutations: { retry: 0 },
    },
  })
}
