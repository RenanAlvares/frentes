import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import type { components } from '@/api/schema'

export type ResultadoBusca = components['schemas']['ResultadoBusca']
export type ItemBusca = components['schemas']['ItemBusca']

/** RN-121: a API exige pelo menos 2 caracteres. */
export const MINIMO_BUSCA = 2

/** Busca global (RN-120); só dispara com o mínimo de caracteres. */
export function useBusca(termo: string) {
  const q = termo.trim()
  return useQuery({
    queryKey: chaves.busca(q),
    queryFn: () => exigir(client.GET('/api/busca', { params: { query: { q } } })),
    enabled: q.length >= MINIMO_BUSCA,
    // Enquanto o novo termo carrega, os resultados anteriores ficam na tela.
    placeholderData: keepPreviousData,
  })
}

/** O valor só muda depois de `ms` sem alterações (não busca a cada tecla). */
export function useAtrasado<T>(valor: T, ms: number): T {
  const [atrasado, setAtrasado] = useState(valor)
  useEffect(() => {
    const espera = setTimeout(() => setAtrasado(valor), ms)
    return () => clearTimeout(espera)
  }, [valor, ms])
  return atrasado
}
