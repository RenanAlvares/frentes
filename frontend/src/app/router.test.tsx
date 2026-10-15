import { screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { renderizarRota, simularSaude } from '@/test/renderizar'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('rotas de 01-produto §3', () => {
  it.each([
    ['/', 'Projetos'],
    ['/hoje', 'Tarefas de hoje'],
    ['/projetos/7', 'Projeto'],
    ['/projetos/7?tarefa=3', 'Projeto'],
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
