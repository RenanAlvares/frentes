import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderizarRota, simularGet } from '@/test/renderizar'

describe('Backup (01 §4.9, RN-110, RN-111)', () => {
  it('Configurações: "Exportar backup" baixa o zip e há a instrução de restauração', async () => {
    simularGet()
    renderizarRota('/configuracoes')

    const secao = within(await screen.findByRole('region', { name: 'Backup' }))
    const exportar = secao.getByRole('link', { name: 'Exportar backup' })
    expect(exportar).toHaveAttribute('href', '/api/backup')
    expect(exportar).toHaveAttribute('download')
    expect(
      secao.getByText('uv run --directory backend frentes restaurar caminho/do/backup.zip'),
    ).toBeInTheDocument()
    expect(secao.getByText(/feche o Frentes/)).toBeInTheDocument()
  })

  it('menu ⋯: "Exportar backup" baixa o zip', async () => {
    simularGet()
    renderizarRota('/')
    const usuario = userEvent.setup()

    await usuario.click(await screen.findByRole('button', { name: 'Menu' }))

    const item = await screen.findByRole('menuitem', { name: 'Exportar backup' })
    expect(item).toHaveAttribute('href', '/api/backup')
    expect(item).toHaveAttribute('download')
  })
})
