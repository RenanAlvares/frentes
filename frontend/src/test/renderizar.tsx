import { render } from '@testing-library/react'
import { createMemoryRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { vi } from 'vitest'
import { Providers } from '@/app/providers'
import { rotas } from '@/app/router'

/** Renderiza o app inteiro (providers + rotas) já na URL informada. */
export function renderizarRota(url = '/') {
  const router = createMemoryRouter(rotas, { initialEntries: [url] })
  return render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  )
}

/** Substitui o fetch global por uma resposta fixa de GET /api/saude. */
export function simularSaude(versao = '1.2.3') {
  const fetchFalso = vi.fn(async () =>
    Response.json({ status: 'ok', versao, hoje: '2026-10-14', hoje_simulado: false }),
  )
  vi.stubGlobal('fetch', fetchFalso)
  return fetchFalso
}
