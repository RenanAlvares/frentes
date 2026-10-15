import type { components } from '@/api/schema'

export type StatusProjeto = components['schemas']['StatusProjeto']

// 01-produto §5 (RN-11).
export const ROTULO_STATUS: Record<StatusProjeto, string> = {
  planejado: 'Planejado',
  em_andamento: 'Em andamento',
  aguardando: 'Aguardando',
  concluido: 'Concluído',
}

export const LISTA_STATUS = Object.keys(ROTULO_STATUS) as StatusProjeto[]
