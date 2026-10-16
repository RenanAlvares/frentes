import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
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

const coluna = (nome: string) => screen.getByRole('region', { name: nome })

describe('QuadroTarefas (01 §4.4)', () => {
  it('três colunas com as tarefas na ordem da API e os contadores', async () => {
    simularGet({
      '/api/projetos/{projeto_id}/tarefas': quadro({
        pendente: [tarefa({ id: 'b', titulo: 'B' }), tarefa({ id: 'a', titulo: 'A' })],
        em_andamento: [tarefa({ id: 'x', titulo: 'X', status: 'em_andamento' })],
        concluida: [tarefa({ id: 'z', titulo: 'Z', status: 'concluida' })],
        total_concluidas: 1,
      }),
    })

    renderizarRota(URL)

    await screen.findByText('B')
    const pendente = within(coluna('Pendente'))
    expect(pendente.getAllByRole('article').map((card) => card.textContent)).toEqual(['B', 'A'])
    expect(pendente.getByText('2')).toBeInTheDocument()
    expect(within(coluna('Em andamento')).getByText('X')).toBeInTheDocument()
    expect(within(coluna('Concluída')).getByText('Z')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Ver todas/ })).not.toBeInTheDocument()
  })

  it('card: prazo vermelho se atrasada, âmbar se vence hoje, e ícone de prioridade', async () => {
    simularGet({
      '/api/projetos/{projeto_id}/tarefas': quadro({
        pendente: [
          tarefa({
            id: '1',
            titulo: 'Atrasada',
            prazo: '2026-10-10',
            atrasada: true,
            prioridade: 'alta',
          }),
          tarefa({ id: '2', titulo: 'Hoje', prazo: '2026-10-14', prioridade: 'baixa' }),
          tarefa({ id: '3', titulo: 'Depois', prazo: '2027-02-01' }),
        ],
      }),
    })

    renderizarRota(URL)

    const card = async (titulo: string) =>
      within((await screen.findByText(titulo)).closest('article')!)
    expect((await card('Atrasada')).getByText('10/10')).toHaveClass('text-red-600')
    expect(
      (await card('Atrasada')).getByRole('img', { name: 'Prioridade alta' }),
    ).toBeInTheDocument()
    expect((await card('Hoje')).getByText('14/10')).toHaveClass('text-amber-600')
    expect((await card('Hoje')).getByRole('img', { name: 'Prioridade baixa' })).toBeInTheDocument()
    expect((await card('Depois')).getByText('01/02/2027')).toHaveClass('text-muted-foreground')
    expect((await card('Depois')).queryByRole('img')).not.toBeInTheDocument()
  })

  it('criação rápida: Enter cria tarefa simples com o título e limpa o campo', async () => {
    simularGet()
    const post = simularEscrita('POST', sucesso(tarefa(), 201))
    const usuario = userEvent.setup()
    renderizarRota(URL)

    const campo = await screen.findByRole('textbox', { name: 'Nova tarefa' })
    await usuario.type(campo, '  Comprar tinta  {Enter}')

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/projetos/{projeto_id}/tarefas', {
        params: { path: { projeto_id: ID } },
        body: { titulo: 'Comprar tinta' },
      }),
    )
    await waitFor(() => expect(campo).toHaveValue(''))
  })

  it('criação rápida: em branco não envia; erro da API aparece abaixo do campo', async () => {
    simularGet()
    const post = simularEscrita(
      'POST',
      falha(422, {
        erro: {
          codigo: 'validacao',
          mensagem: 'Revise os campos destacados.',
          campos: { titulo: 'Use no máximo 200 caracteres.' },
        },
      }),
    )
    const usuario = userEvent.setup()
    renderizarRota(URL)
    const campo = await screen.findByRole('textbox', { name: 'Nova tarefa' })

    await usuario.type(campo, '   {Enter}')
    expect(post).not.toHaveBeenCalled()

    await usuario.type(campo, 'x{Enter}')
    expect(await screen.findByText('Use no máximo 200 caracteres.')).toBeInTheDocument()
    expect(campo).toHaveAttribute('aria-invalid', 'true')
  })

  it('"Ver todas (N)" aparece com mais de 20 concluídas e lista todas', async () => {
    const concluidas = Array.from({ length: 20 }, (_, i) =>
      tarefa({ id: `c${i}`, titulo: `Feita ${i}`, status: 'concluida' }),
    )
    simularGet({
      '/api/projetos/{projeto_id}/tarefas': quadro({ concluida: concluidas, total_concluidas: 22 }),
      '/api/projetos/{projeto_id}/tarefas/concluidas': [
        tarefa({
          id: 'v1',
          titulo: 'A mais antiga',
          status: 'concluida',
          concluida_em: '2026-09-01T15:00:00Z',
        }),
      ],
    })
    renderizarRota(URL)

    const verTodas = await screen.findByRole('button', { name: 'Ver todas (22)' })
    expect(within(coluna('Concluída')).getByText('22')).toBeInTheDocument()
    await userEvent.click(verTodas)

    const dialogo = await screen.findByRole('dialog', { name: 'Tarefas concluídas' })
    expect(await within(dialogo).findByText('A mais antiga')).toBeInTheDocument()
    expect(within(dialogo).getByText('01/09/2026')).toBeInTheDocument()
  })

  it('cards são arrastáveis pelo teclado (Espaço)', async () => {
    simularGet({
      '/api/projetos/{projeto_id}/tarefas': quadro({
        pendente: [tarefa({ titulo: 'Arrastável' })],
      }),
    })

    renderizarRota(URL)

    const card = (await screen.findByText('Arrastável')).closest('[aria-roledescription]')
    expect(card).toHaveAttribute('aria-roledescription', 'sortable')
    expect(card).toHaveAttribute('tabindex', '0')
  })
})
