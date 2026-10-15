import type { components } from '@/api/schema'

export type CorProjeto = components['schemas']['CorProjeto']

// 05-frontend §5 / RN-11: cor do projeto → classe da faixa/ponto.
export const CORES_PROJETO: Record<CorProjeto, { rotulo: string; fundo: string }> = {
  azul: { rotulo: 'Azul', fundo: 'bg-blue-500' },
  verde: { rotulo: 'Verde', fundo: 'bg-emerald-500' },
  roxo: { rotulo: 'Roxo', fundo: 'bg-violet-500' },
  laranja: { rotulo: 'Laranja', fundo: 'bg-orange-500' },
  rosa: { rotulo: 'Rosa', fundo: 'bg-pink-500' },
  vermelho: { rotulo: 'Vermelho', fundo: 'bg-red-500' },
  ciano: { rotulo: 'Ciano', fundo: 'bg-cyan-500' },
  cinza: { rotulo: 'Cinza', fundo: 'bg-slate-400' },
}

export const LISTA_CORES_PROJETO = Object.keys(CORES_PROJETO) as CorProjeto[]
