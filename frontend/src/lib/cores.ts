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

export type AreaProjeto = 'lembretes' | 'tarefas' | 'documentos' | 'anotacoes'

// 05-frontend §5: áreas do projeto (variáveis em index.css).
export const CORES_AREA: Record<AreaProjeto, { fundo: string; texto: string; borda: string }> = {
  lembretes: {
    fundo: 'bg-area-lembretes-suave',
    texto: 'text-area-lembretes',
    borda: 'border-area-lembretes-borda',
  },
  tarefas: {
    fundo: 'bg-area-tarefas-suave',
    texto: 'text-area-tarefas',
    borda: 'border-area-tarefas-borda',
  },
  documentos: {
    fundo: 'bg-area-documentos-suave',
    texto: 'text-area-documentos',
    borda: 'border-area-documentos-borda',
  },
  anotacoes: {
    fundo: 'bg-area-anotacoes-suave',
    texto: 'text-area-anotacoes',
    borda: 'border-area-anotacoes-borda',
  },
}

export type CorAnotacao = components['schemas']['CorAnotacao']

// 05-frontend §5 / RN-80: fundo -100 e borda -300 (amber, blue, emerald, pink, violet, slate).
export const CORES_ANOTACAO: Record<CorAnotacao, { rotulo: string; fundo: string; texto: string }> =
  {
    amarelo: {
      rotulo: 'Amarelo',
      fundo: 'border border-amber-300 bg-amber-100',
      texto: 'text-foreground',
    },
    azul: { rotulo: 'Azul', fundo: 'border border-blue-300 bg-blue-100', texto: 'text-foreground' },
    verde: {
      rotulo: 'Verde',
      fundo: 'border border-emerald-300 bg-emerald-100',
      texto: 'text-foreground',
    },
    rosa: { rotulo: 'Rosa', fundo: 'border border-pink-300 bg-pink-100', texto: 'text-foreground' },
    roxo: {
      rotulo: 'Roxo',
      fundo: 'border border-violet-300 bg-violet-100',
      texto: 'text-foreground',
    },
    cinza: {
      rotulo: 'Cinza',
      fundo: 'border border-slate-300 bg-slate-100',
      texto: 'text-foreground',
    },
  }
