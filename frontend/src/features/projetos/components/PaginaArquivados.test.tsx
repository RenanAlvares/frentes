import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { client } from '@/api/client'
import { projeto, renderizarRota, simularEscrita, simularGet, sucesso } from '@/test/renderizar'

describe('PaginaArquivados (01 §4.7)', () => {
  it('lista os concluídos com a data de conclusão e o link para abrir', async () => {
    const pronto = projeto({
      id: 'p1',
      nome: 'Site antigo',
      status: 'concluido',
      atualizado_em: '2026-10-20T15:00:00Z',
    })
    simularGet({ '/api/projetos': [pronto] })

    renderizarRota('/arquivados')

    expect(await screen.findByText('Site antigo')).toBeInTheDocument()
    expect(screen.getByText('Concluído em 20/10/2026')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Abrir Site antigo' })).toHaveAttribute(
      'href',
      '/projetos/p1',
    )
    expect(client.GET).toHaveBeenCalledWith('/api/projetos', {
      params: { query: { arquivados: true } },
    })
  })

  it('RN-12: Reabrir muda o status para em andamento', async () => {
    const pronto = projeto({ id: 'p1', nome: 'Site antigo', status: 'concluido' })
    simularGet({ '/api/projetos': [pronto] })
    const patch = simularEscrita('PATCH', sucesso({ ...pronto, status: 'em_andamento' }))
    renderizarRota('/arquivados')

    await userEvent.click(await screen.findByRole('button', { name: 'Reabrir Site antigo' }))

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith('/api/projetos/{projeto_id}', {
        params: { path: { projeto_id: 'p1' } },
        body: { status: 'em_andamento' },
      }),
    )
  })

  it('sem arquivados mostra o estado vazio', async () => {
    simularGet({ '/api/projetos': [] })

    renderizarRota('/arquivados')

    expect(await screen.findByText('Nenhum projeto arquivado')).toBeInTheDocument()
  })
})
