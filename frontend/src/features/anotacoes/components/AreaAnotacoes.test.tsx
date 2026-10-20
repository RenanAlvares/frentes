import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import {
  anotacao,
  falha,
  renderizarRota,
  simularEscrita,
  simularGet,
  sucesso,
} from '@/test/renderizar'

const ID = '11111111-1111-4111-8111-111111111111'

function comAnotacoes(anotacoes: ReturnType<typeof anotacao>[] = []) {
  simularGet({ '/api/projetos/{projeto_id}/anotacoes': anotacoes })
  renderizarRota(`/projetos/${ID}`)
  return userEvent.setup()
}

const card = async (rotulo: string) =>
  (await screen.findByRole('button', { name: `Abrir anotação ${rotulo}` })).closest('li')!

describe('Cards de anotação (01 §4.4, RN-81)', () => {
  it('na ordem da API, com cor, título opcional e alfinete nas fixadas', async () => {
    comAnotacoes([
      anotacao({ id: 'a', titulo: 'Senhas', texto: 'Wi-Fi: casa123', cor: 'roxo', fixada: true }),
      anotacao({ id: 'b', titulo: '', texto: 'Comprar parafusos', cor: 'azul' }),
    ])

    const fixada = await card('Senhas')
    expect(fixada).toHaveClass('bg-violet-100', 'border-violet-300')
    // Card compacto: título + uma linha de prévia (o texto completo fica no modal).
    expect(within(fixada).getByText('Senhas')).toHaveClass('truncate')
    expect(within(fixada).getByText('Wi-Fi: casa123')).toHaveClass('truncate')
    expect(within(fixada).getByRole('button', { name: 'Desafixar Senhas' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )

    const semTitulo = await card('Comprar parafusos')
    expect(semTitulo).toHaveClass('bg-blue-100')
    expect(
      within(semTitulo).getByRole('button', { name: 'Fixar Comprar parafusos' }),
    ).toHaveAttribute('aria-pressed', 'false')

    const area = within(screen.getByRole('region', { name: 'Anotações' }))
    expect(area.getAllByRole('listitem')).toEqual([fixada, semTitulo])
  })

  it('sem título: a primeira linha vira o título e o resto, uma linha de prévia', async () => {
    comAnotacoes([anotacao({ titulo: '', texto: 'Medidas da sala\n4 x 5 m\n\npé-direito 2,60 m' })])

    const cartao = await card('Medidas da sala')
    expect(within(cartao).getByText('Medidas da sala')).toHaveClass('truncate', 'font-semibold')
    expect(within(cartao).getByText('4 x 5 m pé-direito 2,60 m')).toHaveClass('truncate')
  })

  it('sem anotações: "Nenhuma anotação."', async () => {
    comAnotacoes()

    expect(await screen.findByText('Nenhuma anotação.')).toBeInTheDocument()
  })

  it('o alfinete fixa na hora, sem abrir o modal (RN-85)', async () => {
    const usuario = comAnotacoes([anotacao({ id: 'n1', titulo: 'Medidas' })])
    const patch = simularEscrita('PATCH', sucesso(anotacao({ fixada: true })))

    await usuario.click(await screen.findByRole('button', { name: 'Fixar Medidas' }))

    expect(patch).toHaveBeenCalledWith('/api/anotacoes/{anotacao_id}', {
      params: { path: { anotacao_id: 'n1' } },
      body: { fixada: true },
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

describe('ModalAnotacao (01 §4.6, RN-80, RN-85)', () => {
  it('"+ Anotação" cria com texto obrigatório, cor e fixar', async () => {
    const usuario = comAnotacoes()
    const post = simularEscrita('POST', sucesso(anotacao(), 201))

    await usuario.click(await screen.findByRole('button', { name: 'Anotação' }))
    const dialogo = within(await screen.findByRole('dialog', { name: 'Nova anotação' }))
    await usuario.click(dialogo.getByRole('button', { name: 'Salvar' }))
    expect(await dialogo.findByText('Escreva o texto da anotação.')).toBeInTheDocument()
    expect(post).not.toHaveBeenCalled()

    expect(dialogo.getByRole('radio', { name: 'Amarelo' })).toHaveAttribute('aria-checked', 'true')
    await usuario.type(dialogo.getByLabelText('Texto *'), 'Tinta: Suvinil Branco Neve')
    await usuario.click(dialogo.getByRole('radio', { name: 'Azul' }))
    await usuario.click(dialogo.getByRole('switch', { name: 'Fixar no topo' }))
    await usuario.click(dialogo.getByRole('button', { name: 'Salvar' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(post).toHaveBeenCalledWith('/api/projetos/{projeto_id}/anotacoes', {
      params: { path: { projeto_id: ID } },
      body: { titulo: '', texto: 'Tinta: Suvinil Branco Neve', cor: 'azul', fixada: true },
    })
  })

  it('clique no card abre a edição; Salvar envia só o que mudou', async () => {
    const usuario = comAnotacoes([anotacao({ id: 'n1', titulo: 'Medidas', texto: 'Sala' })])
    const patch = simularEscrita('PATCH', sucesso(anotacao()))

    await usuario.click(await screen.findByRole('button', { name: 'Abrir anotação Medidas' }))
    const dialogo = within(await screen.findByRole('dialog', { name: 'Editar anotação' }))
    expect(dialogo.getByLabelText('Título')).toHaveValue('Medidas')
    const texto = dialogo.getByLabelText('Texto *')
    expect(texto).toHaveValue('Sala')
    // Texto longo não empurra o Salvar para fora da tela: o campo e o modal rolam.
    expect(texto).toHaveClass('max-h-[50vh]')
    expect(screen.getByRole('dialog')).toHaveClass('max-h-[calc(100dvh-2rem)]', 'overflow-y-auto')
    await usuario.type(texto, ': 4 x 5 m')
    await usuario.click(dialogo.getByRole('button', { name: 'Salvar' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(patch).toHaveBeenCalledWith('/api/anotacoes/{anotacao_id}', {
      params: { path: { anotacao_id: 'n1' } },
      body: { texto: 'Sala: 4 x 5 m' },
    })
  })

  it('erro 422 da API aparece abaixo do campo', async () => {
    const usuario = comAnotacoes([anotacao({ titulo: 'Medidas' })])
    simularEscrita(
      'PATCH',
      falha(422, {
        erro: {
          codigo: 'validacao',
          mensagem: 'Revise os campos destacados.',
          campos: { titulo: 'Use no máximo 120 caracteres.' },
        },
      }),
    )

    await usuario.click(await screen.findByRole('button', { name: 'Abrir anotação Medidas' }))
    const dialogo = within(await screen.findByRole('dialog'))
    await usuario.type(dialogo.getByLabelText('Título'), '!')
    await usuario.click(dialogo.getByRole('button', { name: 'Salvar' }))

    expect(await dialogo.findByText('Use no máximo 120 caracteres.')).toBeInTheDocument()
  })

  it('fechar com alterações pede confirmação; "Descartar" fecha sem salvar', async () => {
    const usuario = comAnotacoes([anotacao({ titulo: 'Medidas' })])
    const patch = simularEscrita('PATCH', sucesso(anotacao()))

    await usuario.click(await screen.findByRole('button', { name: 'Abrir anotação Medidas' }))
    const dialogo = within(await screen.findByRole('dialog'))
    await usuario.type(dialogo.getByLabelText('Texto *'), ' extra')
    await usuario.keyboard('{Escape}')

    const confirmar = await screen.findByRole('alertdialog', { name: 'Descartar alterações?' })
    await usuario.click(within(confirmar).getByRole('button', { name: 'Descartar' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(patch).not.toHaveBeenCalled()
  })

  it('Excluir manda para a lixeira com Desfazer', async () => {
    const usuario = comAnotacoes([anotacao({ id: 'n1', titulo: 'Medidas' })])
    const excluir = simularEscrita('DELETE', sucesso(undefined, 204))
    const restaurar = simularEscrita('POST', sucesso(undefined, 204))

    await usuario.click(await screen.findByRole('button', { name: 'Abrir anotação Medidas' }))
    const dialogo = within(await screen.findByRole('dialog'))
    await usuario.click(dialogo.getByRole('button', { name: 'Excluir' }))

    expect(await screen.findByText('Movido para a lixeira')).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(excluir).toHaveBeenCalledWith('/api/anotacoes/{anotacao_id}', {
      params: { path: { anotacao_id: 'n1' } },
    })
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(restaurar).toHaveBeenCalledWith('/api/lixeira/{tipo}/{item_id}/restaurar', {
        params: { path: { tipo: 'anotacao', item_id: 'n1' } },
      }),
    )
  })
})
