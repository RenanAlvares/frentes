import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { client } from '@/api/client'
import { projeto, renderizarRota, simularEscrita, simularGet, sucesso } from '@/test/renderizar'

const card = (nome: string) => screen.getByRole('heading', { name: nome }).closest('article')!

describe('PaginaProjetos (01 §4.2)', () => {
  it('estado vazio convida a criar o primeiro projeto', async () => {
    simularGet({ '/api/projetos': [] })

    renderizarRota('/')

    expect(await screen.findByText('Crie seu primeiro projeto')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Novo projeto' }))
    expect(await screen.findByRole('dialog', { name: 'Novo projeto' })).toBeInTheDocument()
  })

  it('mostra os cards na ordem da API e o card de novo projeto por último', async () => {
    simularGet({
      '/api/projetos': [
        projeto({ id: 'b', nome: 'B', posicao: 0 }),
        projeto({ id: 'a', nome: 'A', posicao: 1 }),
      ],
    })

    renderizarRota('/')

    await screen.findByRole('heading', { name: 'B' })
    const titulos = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(titulos).toEqual(['B', 'A'])
    expect(screen.getByRole('link', { name: 'B' })).toHaveAttribute('href', '/projetos/b')
    expect(screen.getByRole('button', { name: 'Novo projeto' })).toBeInTheDocument()
  })

  it('card: status, prazo vencido em vermelho (hoje da API), progresso e avisos', async () => {
    simularGet({
      '/api/projetos': [
        projeto({
          nome: 'Atrasado',
          status: 'aguardando',
          prazo: '2026-10-13',
          acompanhar_progresso: true,
          progresso: { concluidas: 6, total: 10 },
          avisos: 2,
        }),
        projeto({ id: 'x', nome: 'Futuro', prazo: '2027-01-05', progresso: null, avisos: 1 }),
      ],
    })

    renderizarRota('/')

    await screen.findByRole('heading', { name: 'Atrasado' })
    const atrasado = within(card('Atrasado'))
    expect(atrasado.getByText('Aguardando')).toBeInTheDocument()
    expect(atrasado.getByText('Prazo 13/10')).toHaveClass('text-red-600')
    expect(atrasado.getByText('6/10 tarefas')).toBeInTheDocument()
    expect(atrasado.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '60')
    expect(atrasado.getByText('2 avisos')).toBeInTheDocument()

    const futuro = within(card('Futuro'))
    expect(futuro.getByText('Prazo 05/01/2027')).not.toHaveClass('text-red-600')
    expect(futuro.queryByRole('progressbar')).not.toBeInTheDocument()
    expect(futuro.getByText('1 aviso')).toBeInTheDocument()
  })

  it('RN-13: acompanhando sem tarefas mostra "Sem tarefas"', async () => {
    simularGet({
      '/api/projetos': [
        projeto({ acompanhar_progresso: true, progresso: { concluidas: 0, total: 0 } }),
      ],
    })

    renderizarRota('/')

    expect(await screen.findByText('Sem tarefas')).toBeInTheDocument()
    expect(screen.queryByText(/avisos?$/)).not.toBeInTheDocument()
  })

  it('excluir pelo menu mostra "Movido para a lixeira" com Desfazer, que restaura', async () => {
    const existente = projeto({ nome: 'Reforma' })
    simularGet({ '/api/projetos': [existente] })
    const excluir = simularEscrita('DELETE', sucesso(undefined, 204))
    const restaurar = simularEscrita('POST', sucesso(undefined, 204))
    const usuario = userEvent.setup()
    renderizarRota('/')

    await usuario.click(await screen.findByRole('button', { name: 'Ações de Reforma' }))
    await usuario.click(await screen.findByRole('menuitem', { name: 'Excluir' }))

    expect(await screen.findByText('Movido para a lixeira')).toBeInTheDocument()
    expect(excluir).toHaveBeenCalledWith('/api/projetos/{projeto_id}', {
      params: { path: { projeto_id: existente.id } },
    })
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(restaurar).toHaveBeenCalledWith('/api/lixeira/{tipo}/{item_id}/restaurar', {
        params: { path: { tipo: 'projeto', item_id: existente.id } },
      }),
    )
    expect(client.GET).toHaveBeenCalledWith('/api/projetos', {
      params: { query: { arquivados: false } },
    })
  })
})
