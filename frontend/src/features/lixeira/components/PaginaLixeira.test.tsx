import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import {
  itemLixeira,
  renderizarRota,
  saude,
  simularEscrita,
  simularGet,
  sucesso,
} from '@/test/renderizar'

type Item = ReturnType<typeof itemLixeira>

function comLixeira(itens: Item[], dias = 30) {
  simularGet({ '/api/lixeira': itens, '/api/saude': saude({ lixeira_dias: dias }) })
  renderizarRota('/lixeira')
  return userEvent.setup()
}

const linha = async (titulo: string) =>
  within((await screen.findByText(titulo, { selector: 'p' })).closest('li')!)

describe('Lista da lixeira (01 §4.8, RN-91, RN-94)', () => {
  it('aviso com os dias da configuração; cada item com tipo, projeto, data e expiração', async () => {
    comLixeira(
      [
        itemLixeira({ tipo: 'tarefa', id: 't1', titulo: 'Pintar', projeto_nome: 'Casa' }),
        itemLixeira({
          tipo: 'projeto',
          id: 'p1',
          titulo: 'Reforma',
          projeto_nome: null,
          dias_para_expirar: 1,
        }),
        itemLixeira({ tipo: 'documento', id: 'd1', titulo: 'Planta.pdf', dias_para_expirar: 0 }),
      ],
      45,
    )

    expect(await screen.findByText('Itens ficam aqui por 45 dias.')).toBeInTheDocument()
    expect(
      (await linha('Pintar')).getByText(
        'Tarefa · Casa · excluído em 14/10/2026 · apagado definitivamente em 30 dias',
      ),
    ).toBeInTheDocument()
    expect(
      (await linha('Reforma')).getByText(
        'Projeto · excluído em 14/10/2026 · apagado definitivamente em 1 dia',
      ),
    ).toBeInTheDocument()
    expect(
      (await linha('Planta.pdf')).getByText(
        /apagado definitivamente na próxima vez que o app abrir/,
      ),
    ).toBeInTheDocument()
  })

  it('vazia: "A lixeira está vazia." e sem "Esvaziar lixeira"', async () => {
    comLixeira([])

    expect(await screen.findByText('A lixeira está vazia.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Esvaziar lixeira' })).not.toBeInTheDocument()
  })
})

describe('Ações (RN-92, RN-93)', () => {
  it('Restaurar chama o endpoint do tipo', async () => {
    const usuario = comLixeira([itemLixeira({ tipo: 'lembrete', id: 'l1', titulo: 'IPTU' })])
    const post = simularEscrita('POST', sucesso(undefined, 204))

    await usuario.click((await linha('IPTU')).getByRole('button', { name: 'Restaurar' }))

    expect(post).toHaveBeenCalledWith('/api/lixeira/{tipo}/{item_id}/restaurar', {
      params: { path: { tipo: 'lembrete', item_id: 'l1' } },
    })
  })

  it('"Excluir agora" pede confirmação; Cancelar não apaga, Excluir apaga', async () => {
    const usuario = comLixeira([itemLixeira({ tipo: 'anotacao', id: 'n1', titulo: 'Medidas' })])
    const apagar = simularEscrita('DELETE', sucesso(undefined, 204))

    await usuario.click((await linha('Medidas')).getByRole('button', { name: 'Excluir agora' }))
    let confirmar = within(
      await screen.findByRole('alertdialog', { name: 'Excluir definitivamente?' }),
    )
    expect(
      confirmar.getByText('“Medidas” será apagado de vez. Não dá para desfazer.'),
    ).toBeInTheDocument()
    await usuario.click(confirmar.getByRole('button', { name: 'Cancelar' }))
    expect(apagar).not.toHaveBeenCalled()

    await usuario.click((await linha('Medidas')).getByRole('button', { name: 'Excluir agora' }))
    confirmar = within(await screen.findByRole('alertdialog'))
    await usuario.click(confirmar.getByRole('button', { name: 'Excluir' }))

    await waitFor(() =>
      expect(apagar).toHaveBeenCalledWith('/api/lixeira/{tipo}/{item_id}', {
        params: { path: { tipo: 'anotacao', item_id: 'n1' } },
      }),
    )
  })

  it('"Esvaziar lixeira" pede confirmação com o total', async () => {
    const usuario = comLixeira([
      itemLixeira({ id: 'a', titulo: 'A' }),
      itemLixeira({ id: 'b', titulo: 'B' }),
    ])
    const apagar = simularEscrita('DELETE', sucesso(undefined, 204))

    await usuario.click(await screen.findByRole('button', { name: 'Esvaziar lixeira' }))
    const confirmar = within(await screen.findByRole('alertdialog', { name: 'Esvaziar lixeira?' }))
    expect(
      confirmar.getByText('Os 2 itens serão apagados de vez. Não dá para desfazer.'),
    ).toBeInTheDocument()
    await usuario.click(confirmar.getByRole('button', { name: 'Esvaziar' }))

    await waitFor(() => expect(apagar).toHaveBeenCalledWith('/api/lixeira'))
  })
})
