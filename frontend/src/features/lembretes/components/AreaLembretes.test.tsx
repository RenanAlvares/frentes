import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { lembrete, renderizarRota, simularEscrita, simularGet, sucesso } from '@/test/renderizar'

const ID = '11111111-1111-4111-8111-111111111111'
const URL = `/projetos/${ID}`

const area = () => within(screen.getByRole('region', { name: 'Lembretes' }))
const item = async (titulo: string) =>
  within((await screen.findByRole('button', { name: titulo })).closest('li')!)

function comLembretes(ativos: ReturnType<typeof lembrete>[], concluidos = [] as typeof ativos) {
  simularGet({ '/api/projetos/{projeto_id}/lembretes': { ativos, concluidos } })
  renderizarRota(URL)
  return userEvent.setup()
}

describe('ItemLembrete (01 §4.4)', () => {
  it('mostra título, data, regra e texto relativo; janela em âmbar e vencido em vermelho', async () => {
    comLembretes([
      lembrete({
        id: 'a',
        titulo: 'Atrasado',
        vencimento: '2026-08-05',
        dias_restantes: -70,
        na_janela: true,
        ocorrencias_atrasadas: 3,
        recorrencia_descricao: 'todo dia 5',
      }),
      lembrete({
        id: 'b',
        titulo: 'Na janela',
        vencimento: '2026-10-16',
        dias_restantes: 2,
        na_janela: true,
      }),
      lembrete({ id: 'c', titulo: 'Longe', vencimento: '2027-01-10', dias_restantes: 88 }),
    ])

    const atrasado = await item('Atrasado')
    expect(atrasado.getByText('05/08 · todo dia 5')).toBeInTheDocument()
    expect(atrasado.getByText('vencido há 70 dias · 3 ocorrências atrasadas')).toHaveClass(
      'text-red-600',
    )
    expect((await screen.findByRole('button', { name: 'Atrasado' })).closest('li')).toHaveClass(
      'border-amber-400',
    )

    const janela = await item('Na janela')
    expect(janela.getByText('vence em 2 dias')).not.toHaveClass('text-red-600')
    expect((await screen.findByRole('button', { name: 'Na janela' })).closest('li')).toHaveClass(
      'border-amber-400',
    )

    const longe = await item('Longe')
    expect(longe.getByText('10/01/2027')).toBeInTheDocument()
    expect((await screen.findByRole('button', { name: 'Longe' })).closest('li')).not.toHaveClass(
      'border-amber-400',
    )
  })

  it('Dar baixa mostra "Baixa registrada" e Desfazer chama desfazer-baixa', async () => {
    const usuario = comLembretes([lembrete({ id: 'l1', titulo: 'IPTU' })])
    const post = simularEscrita('POST', sucesso(lembrete()))

    await usuario.click(await screen.findByRole('button', { name: 'Ações de IPTU' }))
    await usuario.click(await screen.findByRole('menuitem', { name: 'Dar baixa' }))

    expect(await screen.findByText('Baixa registrada')).toBeInTheDocument()
    expect(post).toHaveBeenCalledWith('/api/lembretes/{lembrete_id}/baixa', {
      params: { path: { lembrete_id: 'l1' } },
    })
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/lembretes/{lembrete_id}/desfazer-baixa', {
        params: { path: { lembrete_id: 'l1' } },
      }),
    )
  })

  it('Excluir mostra "Movido para a lixeira" e Desfazer restaura', async () => {
    const usuario = comLembretes([lembrete({ id: 'l1', titulo: 'IPTU' })])
    const excluir = simularEscrita('DELETE', sucesso(undefined, 204))
    const restaurar = simularEscrita('POST', sucesso(undefined, 204))

    await usuario.click(await screen.findByRole('button', { name: 'Ações de IPTU' }))
    await usuario.click(await screen.findByRole('menuitem', { name: 'Excluir' }))

    expect(await screen.findByText('Movido para a lixeira')).toBeInTheDocument()
    expect(excluir).toHaveBeenCalledWith('/api/lembretes/{lembrete_id}', {
      params: { path: { lembrete_id: 'l1' } },
    })
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(restaurar).toHaveBeenCalledWith('/api/lixeira/{tipo}/{item_id}/restaurar', {
        params: { path: { tipo: 'lembrete', item_id: 'l1' } },
      }),
    )
  })
})

describe('Concluídos (01 §4.4)', () => {
  it('seção recolhida com o total; Reativar usa desfazer-baixa (RN-44)', async () => {
    const usuario = comLembretes(
      [],
      [lembrete({ id: 'feito', titulo: 'Renovar CNH', concluido_em: '2026-10-10T15:00:00Z' })],
    )
    const post = simularEscrita('POST', sucesso(lembrete()))

    const secao = await screen.findByRole('button', { name: 'Concluídos (1)' })
    expect(secao).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('Renovar CNH')).not.toBeInTheDocument()
    expect(area().getByText('Nenhum lembrete.')).toBeInTheDocument()

    await usuario.click(secao)
    expect(screen.getByText('Concluído em 10/10/2026')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Reativar Renovar CNH' }))

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/lembretes/{lembrete_id}/desfazer-baixa', {
        params: { path: { lembrete_id: 'feito' } },
      }),
    )
  })
})

describe('ModalLembrete (01 §4.6)', () => {
  it('criar: vencimento obrigatório; antecedência vazia usa o padrão; Repetir manda a regra', async () => {
    const usuario = comLembretes([])
    const post = simularEscrita('POST', sucesso(lembrete(), 201))

    await usuario.click(await screen.findByRole('button', { name: 'Lembrete' }))
    const modal = within(await screen.findByRole('dialog', { name: 'Novo lembrete' }))
    await usuario.type(modal.getByLabelText('Título *'), 'Pagar IPTU')
    await usuario.click(modal.getByRole('button', { name: 'Salvar' }))
    expect(await modal.findByText('Informe o vencimento.')).toBeInTheDocument()

    await usuario.click(modal.getByLabelText('Vencimento *'))
    await usuario.click(within(await screen.findByRole('grid')).getByText('15'))
    await usuario.click(modal.getByRole('switch', { name: 'Repetir' }))
    expect(modal.getByText('Repete todo dia')).toBeInTheDocument()
    await usuario.click(modal.getByRole('button', { name: 'Salvar' }))

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/projetos/{projeto_id}/lembretes', {
        params: { path: { projeto_id: ID } },
        body: {
          titulo: 'Pagar IPTU',
          observacao: '',
          vencimento: expect.stringMatching(/^\d{4}-\d{2}-15$/),
          recorrencia: {
            frequencia: 'diaria',
            intervalo: 1,
            dias_semana: null,
            dia_mes: null,
            mes: null,
          },
        },
      }),
    )
  })

  it('editar: tirar a repetição manda recorrencia null; só o que mudou', async () => {
    const usuario = comLembretes([
      lembrete({
        id: 'l1',
        titulo: 'Regar',
        recorrencia: {
          frequencia: 'diaria',
          intervalo: 2,
          dias_semana: null,
          dia_mes: null,
          mes: null,
        },
        recorrencia_descricao: 'a cada 2 dias',
      }),
    ])
    const patch = simularEscrita('PATCH', sucesso(lembrete()))

    await usuario.click(await screen.findByRole('button', { name: 'Regar' }))
    const modal = within(await screen.findByRole('dialog', { name: 'Editar lembrete' }))
    expect(modal.getByLabelText('Avisar com quantos dias de antecedência')).toHaveValue(3)
    expect(modal.getByText('Repete a cada 2 dias')).toBeInTheDocument()
    await usuario.click(modal.getByRole('switch', { name: 'Repetir' }))
    await usuario.click(modal.getByRole('button', { name: 'Salvar' }))

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith('/api/lembretes/{lembrete_id}', {
        params: { path: { lembrete_id: 'l1' } },
        body: { recorrencia: null },
      }),
    )
  })
})
