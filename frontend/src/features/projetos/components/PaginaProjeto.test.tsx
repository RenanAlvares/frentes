import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import {
  falha,
  projeto,
  renderizarRota,
  simularEscrita,
  simularGet,
  sucesso,
} from '@/test/renderizar'

const ID = '11111111-1111-4111-8111-111111111111'
const URL = `/projetos/${ID}`

describe('PaginaProjeto: cabeçalho (01 §4.4)', () => {
  it('mostra nome, status, datas do ano atual em dd/mm e o progresso', async () => {
    simularGet({
      '/api/projetos/{projeto_id}': projeto({
        nome: 'Reforma',
        status: 'aguardando',
        data_inicio: '2026-10-01',
        prazo: '2027-01-30',
        acompanhar_progresso: true,
        progresso: { concluidas: 6, total: 10 },
      }),
    })

    renderizarRota(URL)

    expect(await screen.findByRole('heading', { level: 1, name: 'Reforma' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Status: Aguardando/ })).toBeInTheDocument()
    expect(screen.getByText('Início 01/10 · Prazo 30/01/2027')).toBeInTheDocument()
    expect(screen.getByText('6/10 tarefas')).toBeInTheDocument()
  })

  it('descrição em uma linha expande ao clicar', async () => {
    simularGet({ '/api/projetos/{projeto_id}': projeto({ descricao: 'Trocar o piso e pintar' }) })
    renderizarRota(URL)

    const descricao = await screen.findByRole('button', { name: 'Trocar o piso e pintar' })
    expect(descricao).toHaveAttribute('aria-expanded', 'false')
    expect(descricao).toHaveClass('truncate')

    await userEvent.click(descricao)

    expect(descricao).toHaveAttribute('aria-expanded', 'true')
    expect(descricao).not.toHaveClass('truncate')
  })

  it('trocar o status pelo chip faz PATCH', async () => {
    simularGet()
    const patch = simularEscrita('PATCH', sucesso(projeto({ status: 'concluido' })))
    const usuario = userEvent.setup()
    renderizarRota(URL)

    await usuario.click(await screen.findByRole('button', { name: /Status: Em andamento/ }))
    await usuario.click(await screen.findByRole('menuitemradio', { name: 'Concluído' }))

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith('/api/projetos/{projeto_id}', {
        params: { path: { projeto_id: ID } },
        body: { status: 'concluido' },
      }),
    )
  })

  it('voltar retorna para a tela anterior', async () => {
    simularGet()
    renderizarRota(['/arquivados', URL])

    await userEvent.click(await screen.findByRole('button', { name: 'Voltar' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Arquivados' })).toBeInTheDocument()
  })

  it('voltar sem histórico vai para a home', async () => {
    simularGet()
    renderizarRota(URL)

    await userEvent.click(await screen.findByRole('button', { name: 'Voltar' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Projetos' })).toBeInTheDocument()
  })

  it('excluir projeto volta para a home com Desfazer', async () => {
    simularGet()
    simularEscrita('DELETE', sucesso(undefined, 204))
    const usuario = userEvent.setup()
    renderizarRota(URL)

    await usuario.click(await screen.findByRole('button', { name: 'Ações do projeto' }))
    await usuario.click(await screen.findByRole('menuitem', { name: 'Excluir projeto' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Projetos' })).toBeInTheDocument()
    expect(await screen.findByText('Movido para a lixeira')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Desfazer' })).toBeInTheDocument()
  })
})

describe('PaginaProjeto: áreas e erros', () => {
  it('mostra as quatro áreas', async () => {
    simularGet()

    renderizarRota(URL)

    expect(
      await within(await screen.findByRole('region', { name: 'Anotações' })).findByText(
        'Nenhuma anotação.',
      ),
    ).toBeInTheDocument()
    expect(
      await within(screen.getByRole('region', { name: 'Documentos' })).findByText(
        'Nenhum documento.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Tarefas' })).toBeInTheDocument()
    expect(
      within(screen.getByRole('region', { name: 'Lembretes' })).getByText('Nenhum lembrete.'),
    ).toBeInTheDocument()
  })

  it('projeto inexistente ou na lixeira mostra "Projeto não encontrado."', async () => {
    simularGet({
      '/api/projetos/{projeto_id}': falha(404, {
        erro: { codigo: 'nao_encontrado', mensagem: 'Projeto não encontrado.' },
      }),
    })

    renderizarRota(URL)

    expect(await screen.findByText('Projeto não encontrado.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Voltar para Projetos' })).toHaveAttribute('href', '/')
  })
})
