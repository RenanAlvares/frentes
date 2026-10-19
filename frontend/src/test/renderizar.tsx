import { render } from '@testing-library/react'
import type { ReactNode } from 'react'
import { createMemoryRouter, MemoryRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { vi } from 'vitest'
import { client } from '@/api/client'
import type { components } from '@/api/schema'
import { Providers } from '@/app/providers'
import { rotas } from '@/app/router'

type Saude = components['schemas']['SaudeResposta']
type Projeto = components['schemas']['Projeto']
type Tarefa = components['schemas']['Tarefa']
type Quadro = components['schemas']['Quadro']

/** Renderiza o app inteiro (providers + rotas) na URL informada (lista = histórico; a última é a atual). */
export function renderizarRota(url: string | string[] = '/') {
  const historico = Array.isArray(url) ? url : [url]
  const router = createMemoryRouter(rotas, {
    initialEntries: historico,
    initialIndex: historico.length - 1,
  })
  return render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  )
}

/** Renderiza um componente com os providers e um roteador em memória. */
export function renderizarComProviders(ui: ReactNode) {
  return render(
    <Providers>
      <MemoryRouter>{ui}</MemoryRouter>
    </Providers>,
  )
}

/** Resposta de sucesso ou de erro (corpo no formato de 04-api) de uma rota simulada. */
export function sucesso(dados: unknown, status = 200) {
  return { data: dados, response: new Response(null, { status }) }
}

export function falha(status: number, erro: unknown) {
  return { error: erro, response: new Response(null, { status }) }
}

/**
 * Simula os GET da API no nível do client (07 §4: não testar a biblioteca).
 * A chave é a rota como no schema (ex.: "/api/projetos/{projeto_id}").
 */
export function simularGet(respostas: Record<string, unknown> = {}) {
  const todas: Record<string, unknown> = {
    '/api/saude': saude(),
    '/api/projetos': [],
    '/api/projetos/{projeto_id}': projeto(),
    '/api/projetos/{projeto_id}/tarefas': quadro(),
    '/api/tarefas/{tarefa_id}': { ...tarefa(), execucoes: [] },
    '/api/projetos/{projeto_id}/lembretes': { ativos: [], concluidos: [] },
    '/api/avisos': { total: 0, itens: [] },
    ...respostas,
  }
  return vi.spyOn(client, 'GET').mockImplementation((async (caminho: string) => {
    if (!(caminho in todas)) throw new Error(`GET ${caminho} não simulado no teste`)
    const valor = todas[caminho]
    // Aceita os dados (sucesso) ou uma resposta pronta, como `falha(404, ...)`.
    const pronta = typeof valor === 'object' && valor !== null && 'response' in valor
    return pronta ? valor : sucesso(valor)
  }) as never)
}

/** Simula uma escrita (POST/PATCH/PUT/DELETE) com a resposta dada. */
export function simularEscrita(
  metodo: 'POST' | 'PATCH' | 'PUT' | 'DELETE',
  resposta: ReturnType<typeof sucesso> | ReturnType<typeof falha>,
) {
  return vi.spyOn(client, metodo).mockResolvedValue(resposta as never)
}

export function simularSaude(dados: Partial<Saude> = {}) {
  return simularGet({ '/api/saude': saude(dados) })
}

export function saude(dados: Partial<Saude> = {}): Saude {
  return { status: 'ok', versao: '1.2.3', hoje: '2026-10-14', hoje_simulado: false, ...dados }
}

export function projeto(dados: Partial<Projeto> = {}): Projeto {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    nome: 'Reforma',
    descricao: '',
    status: 'em_andamento',
    cor: 'azul',
    data_inicio: null,
    prazo: null,
    acompanhar_progresso: false,
    progresso: null,
    avisos: 0,
    posicao: 0,
    criado_em: '2026-10-14T15:00:00Z',
    atualizado_em: '2026-10-14T15:00:00Z',
    ...dados,
  }
}

export function tarefa(dados: Partial<Tarefa> = {}): Tarefa {
  return {
    id: 't1',
    projeto_id: '11111111-1111-4111-8111-111111111111',
    titulo: 'Comprar tinta',
    descricao: '',
    status: 'pendente',
    prioridade: 'media',
    tipo: 'simples',
    prazo: null,
    recorrencia: null,
    recorrencia_descricao: null,
    meta_mensal: null,
    progresso_mes: null,
    posicao: 0,
    concluida_em: null,
    atrasada: false,
    criado_em: '2026-10-14T15:00:00Z',
    atualizado_em: '2026-10-14T15:00:00Z',
    ...dados,
  }
}

export function quadro(dados: Partial<Quadro> = {}): Quadro {
  return { pendente: [], em_andamento: [], concluida: [], total_concluidas: 0, ...dados }
}

type Aviso = components['schemas']['Aviso']
type Lembrete = components['schemas']['Lembrete']

export function lembrete(dados: Partial<Lembrete> = {}): Lembrete {
  return {
    id: 'l1',
    projeto_id: '11111111-1111-4111-8111-111111111111',
    titulo: 'Pagar IPTU',
    observacao: '',
    vencimento: '2026-10-20',
    antecedencia_dias: 3,
    recorrencia: null,
    recorrencia_descricao: null,
    dias_restantes: 6,
    na_janela: false,
    ocorrencias_atrasadas: 0,
    concluido_em: null,
    criado_em: '2026-10-14T15:00:00Z',
    atualizado_em: '2026-10-14T15:00:00Z',
    ...dados,
  }
}

export function aviso(dados: Partial<Aviso> = {}): Aviso {
  return {
    tipo: 'lembrete',
    id: 'a1',
    titulo: 'Pagar IPTU',
    projeto: { id: '11111111-1111-4111-8111-111111111111', nome: 'Reforma', cor: 'azul' },
    vencimento: '2026-10-17',
    dias_restantes: 3,
    ocorrencias_atrasadas: 0,
    meta: null,
    ...dados,
  }
}

export function avisos(...itens: Aviso[]) {
  return { total: itens.length, itens }
}
