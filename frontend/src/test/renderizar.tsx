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

/** Renderiza o app inteiro (providers + rotas) já na URL informada. */
export function renderizarRota(url = '/') {
  const router = createMemoryRouter(rotas, { initialEntries: [url] })
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
    ...respostas,
  }
  return vi.spyOn(client, 'GET').mockImplementation((async (caminho: string) => {
    if (!(caminho in todas)) throw new Error(`GET ${caminho} não simulado no teste`)
    return sucesso(todas[caminho])
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
