import { render } from '@testing-library/react'
import { createMemoryRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { vi } from 'vitest'
import { client } from '@/api/client'
import type { components } from '@/api/schema'
import { Providers } from '@/app/providers'
import { rotas } from '@/app/router'

type Saude = components['schemas']['SaudeResposta']

/** Renderiza o app inteiro (providers + rotas) já na URL informada. */
export function renderizarRota(url = '/') {
  const router = createMemoryRouter(rotas, { initialEntries: [url] })
  return render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  )
}

/** Simula GET /api/saude no nível do client (07 §4: não testar a biblioteca). */
export function simularSaude(saude: Partial<Saude> = {}) {
  const dados: Saude = {
    status: 'ok',
    versao: '1.2.3',
    hoje: '2026-10-14',
    hoje_simulado: false,
    ...saude,
  }
  // O tipo de retorno do client é genérico por rota; aqui só existe a resposta de /api/saude.
  return vi
    .spyOn(client, 'GET')
    .mockResolvedValue({ data: dados, response: new Response() } as never)
}
