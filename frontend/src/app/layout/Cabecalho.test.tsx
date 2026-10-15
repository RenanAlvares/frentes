import { screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { renderizarRota, simularSaude } from '@/test/renderizar'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Cabecalho', () => {
  it('mostra a versão vinda de /api/saude', async () => {
    const fetchFalso = simularSaude('1.2.3')

    renderizarRota('/')

    expect(await screen.findByText('v1.2.3')).toBeInTheDocument()
    expect(fetchFalso).toHaveBeenCalledWith('/api/saude')
  })

  it('marca a aba da rota atual', async () => {
    simularSaude()

    renderizarRota('/hoje')

    expect(await screen.findByRole('link', { name: 'Tarefas de hoje' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('link', { name: 'Projetos' })).not.toHaveAttribute('aria-current')
  })
})
