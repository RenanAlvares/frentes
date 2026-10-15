import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { renderizarRota, simularSaude } from '@/test/renderizar'

describe('Cabecalho', () => {
  it('mostra a versão vinda de /api/saude pelo client tipado', async () => {
    const get = simularSaude({ versao: '1.2.3' })

    renderizarRota('/')

    expect(await screen.findByText('v1.2.3')).toBeInTheDocument()
    expect(get).toHaveBeenCalledWith('/api/saude')
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

  it('mostra a faixa de data simulada quando a API indica hoje_simulado', async () => {
    simularSaude({ hoje: '2026-10-31', hoje_simulado: true })

    renderizarRota('/')

    expect(await screen.findByRole('status')).toHaveTextContent('Data simulada: 31/10/2026')
  })

  it('não mostra a faixa com a data real', async () => {
    simularSaude({ hoje_simulado: false })

    renderizarRota('/')

    await screen.findByText('v1.2.3')
    expect(screen.queryByText(/Data simulada/)).not.toBeInTheDocument()
  })
})
