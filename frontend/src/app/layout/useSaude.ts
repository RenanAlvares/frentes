import { useQuery } from '@tanstack/react-query'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'

export function useSaude() {
  return useQuery({
    queryKey: chaves.saude(),
    queryFn: () => exigir(client.GET('/api/saude')),
  })
}
