import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { renderizarRota, simularSaude } from '@/test/renderizar'

describe('rotas de 01-produto §3', () => {
  it.each([
    ['/', 'Projetos'],
    ['/hoje', 'Tarefas de hoje'],
    ['/projetos/7', 'Reforma'],
    ['/arquivados', 'Arquivados'],
    ['/lixeira', 'Lixeira'],
    ['/configuracoes', 'Configurações'],
  ])('%s abre a tela "%s" dentro do layout', async (url, titulo) => {
    simularSaude()

    renderizarRota(url)

    expect(await screen.findByRole('heading', { level: 1, name: titulo })).toBeInTheDocument()
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })
})
