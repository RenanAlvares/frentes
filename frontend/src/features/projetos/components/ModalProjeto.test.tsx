import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ModalProjeto } from '@/features/projetos/components/ModalProjeto'
import {
  falha,
  projeto,
  renderizarComProviders,
  simularEscrita,
  simularGet,
  sucesso,
} from '@/test/renderizar'

function abrir(props: { projetoId?: string } = {}) {
  const onFechar = vi.fn()
  renderizarComProviders(<ModalProjeto aberto onFechar={onFechar} {...props} />)
  return { onFechar, usuario: userEvent.setup() }
}

const salvar = () => screen.getByRole('button', { name: 'Salvar' })

describe('ModalProjeto: criar', () => {
  it('envia os valores do formulário com os padrões de RN-11 e fecha', async () => {
    simularGet()
    const post = simularEscrita('POST', sucesso(projeto(), 201))
    const { onFechar, usuario } = abrir()

    await usuario.type(screen.getByLabelText('Nome *'), '  Reforma  ')
    await usuario.click(screen.getByRole('radio', { name: 'Roxo' }))
    await usuario.click(screen.getByRole('switch', { name: 'Acompanhar progresso' }))
    await usuario.click(salvar())

    await waitFor(() => expect(onFechar).toHaveBeenCalled())
    expect(post).toHaveBeenCalledWith('/api/projetos', {
      body: {
        nome: 'Reforma',
        descricao: '',
        status: 'em_andamento',
        cor: 'roxo',
        data_inicio: null,
        prazo: null,
        acompanhar_progresso: true,
      },
    })
  })

  it('RN-10: nome vazio mostra o erro abaixo do campo e não envia', async () => {
    simularGet()
    const post = simularEscrita('POST', sucesso(projeto(), 201))
    const { onFechar, usuario } = abrir()

    await usuario.type(screen.getByLabelText('Nome *'), '   ')
    await usuario.click(salvar())

    expect(await screen.findByText('Informe o nome do projeto.')).toBeInTheDocument()
    expect(screen.getByLabelText('Nome *')).toHaveAttribute('aria-invalid', 'true')
    expect(post).not.toHaveBeenCalled()
    expect(onFechar).not.toHaveBeenCalled()
  })

  it('422 da API aparece abaixo do campo e o modal continua aberto', async () => {
    simularGet()
    simularEscrita(
      'POST',
      falha(422, {
        erro: {
          codigo: 'validacao',
          mensagem: 'Revise os campos destacados.',
          campos: { prazo: 'O prazo não pode ser anterior ao início.' },
        },
      }),
    )
    const { onFechar, usuario } = abrir()

    await usuario.type(screen.getByLabelText('Nome *'), 'Reforma')
    await usuario.click(salvar())

    expect(await screen.findByText('O prazo não pode ser anterior ao início.')).toBeInTheDocument()
    expect(onFechar).not.toHaveBeenCalled()
  })

  it('erro sem campos vira toast com a mensagem da API', async () => {
    simularGet()
    simularEscrita('POST', falha(409, { erro: { codigo: 'conflito', mensagem: 'Não deu.' } }))
    const { usuario } = abrir()

    await usuario.type(screen.getByLabelText('Nome *'), 'Reforma')
    await usuario.click(salvar())

    expect(await screen.findByText('Não deu.')).toBeInTheDocument()
  })
})

describe('ModalProjeto: editar', () => {
  const existente = projeto({ nome: 'Site', descricao: 'Antiga', prazo: '2026-12-20' })

  it('carrega o projeto e envia só os campos alterados', async () => {
    simularGet({ '/api/projetos/{projeto_id}': existente })
    const patch = simularEscrita('PATCH', sucesso(existente))
    const { onFechar, usuario } = abrir({ projetoId: existente.id })

    const nome = await screen.findByLabelText('Nome *')
    expect(nome).toHaveValue('Site')
    expect(screen.getByLabelText('Prazo')).toHaveTextContent('20/12/2026')
    await usuario.clear(nome)
    await usuario.type(nome, 'Site novo')
    await usuario.click(salvar())

    await waitFor(() => expect(onFechar).toHaveBeenCalled())
    expect(patch).toHaveBeenCalledWith('/api/projetos/{projeto_id}', {
      params: { path: { projeto_id: existente.id } },
      body: { nome: 'Site novo' },
    })
  })

  it('RN-16: início depois do prazo mostra o erro no prazo antes de enviar', async () => {
    simularGet({
      '/api/projetos/{projeto_id}': projeto({ data_inicio: '2026-12-01', prazo: '2026-12-20' }),
    })
    const patch = simularEscrita('PATCH', sucesso(existente))
    const { usuario } = abrir({ projetoId: existente.id })

    // O calendário abre no mês da data atual (dezembro/2026); escolhe o dia 25.
    await usuario.click(await screen.findByLabelText('Data de início'))
    await usuario.click(within(await screen.findByRole('grid')).getByText('25'))
    expect(screen.getByLabelText('Data de início')).toHaveTextContent('25/12/2026')
    await usuario.click(salvar())

    expect(await screen.findByText('O prazo não pode ser anterior ao início.')).toBeInTheDocument()
    expect(patch).not.toHaveBeenCalled()
  })
})

describe('ModalProjeto: RN-85 fechar', () => {
  it('sem alterações, Cancelar fecha direto', async () => {
    simularGet()
    const { onFechar, usuario } = abrir()

    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(onFechar).toHaveBeenCalled()
    expect(screen.queryByText('Descartar alterações?')).not.toBeInTheDocument()
  })

  it('com alterações pede confirmação; continuar mantém, descartar fecha', async () => {
    simularGet()
    const { onFechar, usuario } = abrir()
    await usuario.type(screen.getByLabelText('Nome *'), 'Rascunho')

    await usuario.keyboard('{Escape}')
    expect(await screen.findByText('Descartar alterações?')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Continuar editando' }))
    expect(onFechar).not.toHaveBeenCalled()
    expect(screen.getByLabelText('Nome *')).toHaveValue('Rascunho')

    await usuario.click(screen.getByRole('button', { name: 'Cancelar' }))
    await usuario.click(await screen.findByRole('button', { name: 'Descartar' }))
    expect(onFechar).toHaveBeenCalled()
  })
})
