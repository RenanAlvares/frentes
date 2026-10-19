import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef, useState } from 'react'
import { chaves } from '@/api/chaves'
import { client, exigir } from '@/api/client'
import type { components } from '@/api/schema'
import { useSaude } from '@/app/layout/useSaude'

export type Aviso = components['schemas']['Aviso']

export function useAvisos() {
  return useQuery({
    queryKey: chaves.avisos(),
    queryFn: () => exigir(client.GET('/api/avisos')),
  })
}

/** Chave de um aviso na lista (lembrete e tarefa podem, em tese, ter o mesmo id). */
export const chaveDoAviso = (aviso: Pick<Aviso, 'tipo' | 'id'>) => `${aviso.tipo}:${aviso.id}`

/**
 * Estado do painel e do sino (05 §8), só em memória: zera ao recarregar (RN-52/53).
 * - `fechado`: "Fechar" oculta o painel; o sino reabre.
 * - `tratados`: itens que receberam uma ação no painel saem da lista até o próximo acesso (RN-54).
 * Ao voltar o foco, se o `hoje` da API mudou, busca os avisos de novo e reabre (RN-53).
 */
export function usePainelAvisos() {
  const queryClient = useQueryClient()
  const { data: avisos } = useAvisos()
  const { data: saude, refetch: buscarSaude } = useSaude()
  const [fechado, setFechado] = useState(false)
  const [tratados, setTratados] = useState<ReadonlySet<string>>(new Set())

  // Novo dia = novo acesso: reabre e devolve à lista o que foi tratado (ajuste de estado no render).
  const hoje = saude?.hoje
  const [diaVisto, setDiaVisto] = useState(hoje)
  if (hoje !== undefined && hoje !== diaVisto) {
    setDiaVisto(hoje)
    if (diaVisto !== undefined) {
      setFechado(false)
      setTratados(new Set())
    }
  }

  const ultimoDia = useRef(hoje)
  useEffect(() => {
    if (hoje === undefined) return
    if (ultimoDia.current !== undefined && ultimoDia.current !== hoje) {
      void queryClient.invalidateQueries({ queryKey: chaves.avisos() })
    }
    ultimoDia.current = hoje
  }, [hoje, queryClient])

  useEffect(() => {
    const verificar = () => {
      if (document.visibilityState !== 'hidden') void buscarSaude()
    }
    window.addEventListener('focus', verificar)
    document.addEventListener('visibilitychange', verificar)
    return () => {
      window.removeEventListener('focus', verificar)
      document.removeEventListener('visibilitychange', verificar)
    }
  }, [buscarSaude])

  const marcar = useCallback((chave: string, tratado: boolean) => {
    setTratados((atuais) => {
      const novos = new Set(atuais)
      if (tratado) novos.add(chave)
      else novos.delete(chave)
      return novos
    })
  }, [])

  const itens = (avisos?.itens ?? []).filter((aviso) => !tratados.has(chaveDoAviso(aviso)))
  return {
    itens,
    fechado,
    fechar: () => setFechado(true),
    abrir: () => setFechado(false),
    /** RN-54: tira o item do painel após a ação; `false` devolve (Desfazer). */
    marcar,
  }
}
