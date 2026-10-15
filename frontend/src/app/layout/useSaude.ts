import { useQuery } from '@tanstack/react-query'

// Provisório: na tarefa 0.4 passa a usar o client tipado e as chaves de api/chaves.ts.
type Saude = { versao: string }

async function buscarSaude(): Promise<Saude> {
  const resposta = await fetch('/api/saude')
  if (!resposta.ok) {
    throw new Error(`GET /api/saude respondeu ${resposta.status}`)
  }
  return (await resposta.json()) as Saude
}

export function useSaude() {
  return useQuery({ queryKey: ['saude'], queryFn: buscarSaude })
}
