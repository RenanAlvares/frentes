import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { client } from '@/api/client'
import {
  falha,
  quadro,
  renderizarRota,
  simularEscrita,
  simularGet,
  sucesso,
  tarefa,
} from '@/test/renderizar'

const ID = '11111111-1111-4111-8111-111111111111'
const URL = `/projetos/${ID}`
const existente = tarefa({
  id: 't1',
  titulo: 'Comprar tinta',
  descricao: 'Branco gelo',
  prioridade: 'alta',
  prazo: '2026-10-20',
})

function abrirPelaUrl(dados = existente) {
  simularGet({ '/api/tarefas/{tarefa_id}': { ...dados, execucoes: [] } })
  renderizarRota(`${URL}?tarefa=${dados.id}`)
  return userEvent.setup()
}

const dialogo = () => screen.findByRole('dialog', { name: 'Tarefa' })
const salvar = () => screen.getByRole('button', { name: 'Salvar' })

describe('ModalTarefa (01 §4.5)', () => {
  it('abre por ?tarefa= com título, chips de status/prioridade/prazo, tipo e descrição', async () => {
    abrirPelaUrl()

    const modal = within(await dialogo())
    expect(await modal.findByLabelText('Título')).toHaveValue('Comprar tinta')
    expect(modal.getByLabelText('Status')).toHaveTextContent('Pendente')
    expect(modal.getByLabelText('Prioridade')).toHaveTextContent('Prioridade alta')
    expect(modal.getByLabelText('Prazo')).toHaveTextContent('20/10/2026')
    expect(modal.getByLabelText('Tipo')).toHaveTextContent('Simples')
    expect(modal.getByLabelText('Descrição')).toHaveValue('Branco gelo')
    expect(client.GET).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}', {
      params: { path: { tarefa_id: 't1' } },
    })
  })

  it('clicar no card do quadro abre o modal da tarefa', async () => {
    simularGet({
      '/api/projetos/{projeto_id}/tarefas': quadro({ pendente: [existente] }),
      '/api/tarefas/{tarefa_id}': { ...existente, execucoes: [] },
    })
    renderizarRota(URL)

    await userEvent.click(await screen.findByText('Comprar tinta'))

    expect(await within(await dialogo()).findByLabelText('Título')).toHaveValue('Comprar tinta')
  })

  it('Salvar envia só o que mudou e fecha', async () => {
    const usuario = abrirPelaUrl()
    const patch = simularEscrita('PATCH', sucesso(existente))
    const titulo = await within(await dialogo()).findByLabelText('Título')

    await usuario.clear(titulo)
    await usuario.type(titulo, 'Pincel')
    await usuario.click(salvar())

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}', {
        params: { path: { tarefa_id: 't1' } },
        body: { titulo: 'Pincel' },
      }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('RN-20: título vazio mostra o erro e não envia; 422 da API vai para o campo', async () => {
    const usuario = abrirPelaUrl()
    const patch = simularEscrita(
      'PATCH',
      falha(422, {
        erro: {
          codigo: 'validacao',
          mensagem: 'Revise os campos destacados.',
          campos: { descricao: 'Use no máximo 5000 caracteres.' },
        },
      }),
    )
    const titulo = await within(await dialogo()).findByLabelText('Título')

    await usuario.clear(titulo)
    await usuario.click(salvar())
    expect(await screen.findByText('Informe o título da tarefa.')).toBeInTheDocument()
    expect(patch).not.toHaveBeenCalled()

    await usuario.type(titulo, 'Outro')
    await usuario.click(salvar())
    expect(await screen.findByText('Use no máximo 5000 caracteres.')).toBeInTheDocument()
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('Concluir fecha o modal e o toast "Tarefa concluída" desfaz', async () => {
    const usuario = abrirPelaUrl()
    const post = simularEscrita('POST', sucesso({ ...existente, status: 'concluida' }))

    await usuario.click(await within(await dialogo()).findByRole('button', { name: 'Concluir' }))

    expect(await screen.findByText('Tarefa concluída')).toBeInTheDocument()
    expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/concluir', {
      params: { path: { tarefa_id: 't1' } },
    })
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/desfazer-conclusao', {
        params: { path: { tarefa_id: 't1' } },
      }),
    )
  })

  it('tarefa concluída não mostra Concluir', async () => {
    abrirPelaUrl({ ...existente, status: 'concluida' })

    const modal = within(await dialogo())
    await modal.findByLabelText('Título')
    expect(modal.queryByRole('button', { name: 'Concluir' })).not.toBeInTheDocument()
  })

  it('Excluir mostra "Movido para a lixeira" e Desfazer restaura a tarefa', async () => {
    const usuario = abrirPelaUrl()
    const excluir = simularEscrita('DELETE', sucesso(undefined, 204))
    const restaurar = simularEscrita('POST', sucesso(undefined, 204))

    await usuario.click(await within(await dialogo()).findByRole('button', { name: 'Excluir' }))

    expect(await screen.findByText('Movido para a lixeira')).toBeInTheDocument()
    expect(excluir).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}', {
      params: { path: { tarefa_id: 't1' } },
    })
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(restaurar).toHaveBeenCalledWith('/api/lixeira/{tipo}/{item_id}/restaurar', {
        params: { path: { tipo: 'tarefa', item_id: 't1' } },
      }),
    )
  })

  it('RN-85: com alterações, fechar e concluir pedem confirmação', async () => {
    const usuario = abrirPelaUrl()
    const post = simularEscrita('POST', sucesso(existente))
    const titulo = await within(await dialogo()).findByLabelText('Título')
    await usuario.type(titulo, ' e pincel')

    await usuario.keyboard('{Escape}')
    expect(await screen.findByText('Descartar alterações?')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Continuar editando' }))
    expect(screen.getByLabelText('Título')).toHaveValue('Comprar tinta e pincel')

    await usuario.click(screen.getByRole('button', { name: 'Concluir' }))
    await usuario.click(await screen.findByRole('button', { name: 'Descartar' }))
    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/concluir', {
        params: { path: { tarefa_id: 't1' } },
      }),
    )
  })

  it('tarefa inexistente ou na lixeira', async () => {
    simularGet({
      '/api/tarefas/{tarefa_id}': falha(404, {
        erro: { codigo: 'nao_encontrado', mensagem: 'Tarefa não encontrada.' },
      }),
    })

    renderizarRota(`${URL}?tarefa=sumiu`)

    expect(await within(await dialogo()).findByText('Tarefa não encontrada.')).toBeInTheDocument()
  })
})

describe('ModalTarefa: criação (botão "Nova tarefa")', () => {
  it('cria tarefa simples com título, descrição, prioridade e prazo', async () => {
    simularGet()
    const post = simularEscrita('POST', sucesso(existente, 201))
    const usuario = userEvent.setup()
    renderizarRota(URL)

    await usuario.click(await screen.findByRole('button', { name: 'Nova tarefa' }))
    const modal = within(await screen.findByRole('dialog', { name: 'Nova tarefa' }))
    expect(modal.queryByLabelText('Status')).not.toBeInTheDocument()
    expect(modal.queryByRole('button', { name: 'Excluir' })).not.toBeInTheDocument()
    await usuario.type(modal.getByLabelText('Título'), '  Pintar a sala  ')
    await usuario.type(modal.getByLabelText('Descrição'), 'Duas demãos')
    await usuario.click(modal.getByRole('button', { name: 'Salvar' }))

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/projetos/{projeto_id}/tarefas', {
        params: { path: { projeto_id: ID } },
        body: {
          titulo: 'Pintar a sala',
          descricao: 'Duas demãos',
          prioridade: 'media',
          tipo: 'simples',
          prazo: null,
          recorrencia: null,
          meta_mensal: null,
        },
      }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })
})
