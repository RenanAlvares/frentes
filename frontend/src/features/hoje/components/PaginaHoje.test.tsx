import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import {
  renderizarRota,
  simularEscrita,
  simularGet,
  sucesso,
  tarefa,
  tarefaHoje,
} from '@/test/renderizar'

type Item = ReturnType<typeof tarefaHoje>

function comHoje(
  { atrasadas = [], hoje = [] }: { atrasadas?: Item[]; hoje?: Item[] },
  url = '/hoje',
) {
  simularGet({ '/api/tarefas/hoje': { atrasadas, hoje } })
  const tela = renderizarRota(url)
  return { usuario: userEvent.setup(), ...tela }
}

const atrasadas = [
  tarefaHoje({ id: 'a1', titulo: 'Pagar conta', prazo: '2026-10-01' }),
  tarefaHoje({ id: 'a2', titulo: 'Ligar pro pintor', prazo: '2026-10-12' }),
]

beforeEach(() => sessionStorage.clear())

describe('Linha "N atrasadas" (01 §4.3, RN-61)', () => {
  it('oculta quando não há atrasadas', async () => {
    comHoje({ hoje: [tarefaHoje({ titulo: 'Hoje' })] })

    expect(await screen.findByText('Hoje', { selector: 'button' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /atrasada/ })).not.toBeInTheDocument()
  })

  it('recolhida em vermelho; clique expande e o estado vale na sessão', async () => {
    const { usuario, unmount } = comHoje({ atrasadas })

    const linha = await screen.findByRole('button', { name: '2 atrasadas' })
    expect(linha).toHaveClass('text-red-600')
    expect(linha).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('Pagar conta')).not.toBeInTheDocument()

    await usuario.click(linha)

    expect(linha).toHaveAttribute('aria-expanded', 'true')
    const lista = within(screen.getByRole('region', { name: 'Atrasadas' }))
    expect(lista.getAllByRole('listitem').map((li) => li.textContent)).toEqual([
      expect.stringContaining('Pagar conta'),
      expect.stringContaining('Ligar pro pintor'),
    ])

    unmount()
    comHoje({ atrasadas: atrasadas.slice(0, 1) })
    expect(await screen.findByRole('button', { name: '1 atrasada' })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
    expect(screen.getByText('Pagar conta')).toBeInTheDocument()
  })
})

describe('Lista "Hoje" (01 §4.3, RN-60)', () => {
  it('cada item: título, chip do projeto, prioridade alta, "repete" e "meta 2/4"', async () => {
    comHoje({
      hoje: [
        tarefaHoje({ id: 'h1', titulo: 'Urgente', prioridade: 'alta' }),
        tarefaHoje({
          id: 'h2',
          titulo: 'Regar',
          tipo: 'repetida',
          recorrencia_descricao: 'Toda quarta',
        }),
        tarefaHoje({
          id: 'h3',
          titulo: 'Correr',
          tipo: 'meta_mensal',
          prazo: null,
          meta_mensal: 4,
          progresso_mes: 2,
          projeto: { id: 'p2', nome: 'Saúde', cor: 'verde' },
        }),
      ],
    })
    const item = async (titulo: string) =>
      within((await screen.findByRole('button', { name: titulo })).closest('li')!)

    const urgente = await item('Urgente')
    expect(urgente.getByRole('img', { name: 'Prioridade alta' })).toBeInTheDocument()
    expect(urgente.getByText('Reforma')).toBeInTheDocument()
    expect((await item('Regar')).getByText('repete')).toBeInTheDocument()
    const meta = await item('Correr')
    expect(meta.getByText('meta 2/4')).toBeInTheDocument()
    expect(meta.getByText('Saúde')).toBeInTheDocument()
    expect(meta.queryByRole('img', { name: 'Prioridade alta' })).not.toBeInTheDocument()
  })

  it('estado vazio: "Nada para hoje. Bom trabalho."', async () => {
    comHoje({})

    expect(await screen.findByText('Nada para hoje. Bom trabalho.')).toBeInTheDocument()
  })

  it('checkbox conclui com Desfazer (RN-26); na meta é o +1', async () => {
    const { usuario } = comHoje({
      hoje: [
        tarefaHoje({ id: 'h1', titulo: 'Pintar' }),
        tarefaHoje({
          id: 'm1',
          titulo: 'Correr',
          tipo: 'meta_mensal',
          meta_mensal: 4,
          progresso_mes: 3,
        }),
      ],
    })
    const post = simularEscrita('POST', sucesso(tarefa()))

    await usuario.click(await screen.findByRole('checkbox', { name: 'Concluir Pintar' }))

    expect(await screen.findByText('Tarefa concluída')).toBeInTheDocument()
    expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/concluir', {
      params: { path: { tarefa_id: 'h1' } },
    })
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/desfazer-conclusao', {
        params: { path: { tarefa_id: 'h1' } },
      }),
    )

    await usuario.click(screen.getByRole('checkbox', { name: '+1 em Correr' }))

    expect(await screen.findByText('+1 registrado')).toBeInTheDocument()
    expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/concluir', {
      params: { path: { tarefa_id: 'm1' } },
    })
  })

  it('clique no título abre o modal da tarefa na própria tela', async () => {
    const { usuario } = comHoje({ hoje: [tarefaHoje({ id: 't1', titulo: 'Comprar tinta' })] })

    await usuario.click(await screen.findByRole('button', { name: 'Comprar tinta' }))

    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByDisplayValue('Comprar tinta')).toBeInTheDocument()
    // A lista continua por baixo (o diálogo só a esconde da árvore de acessibilidade).
    expect(
      screen.getByRole('heading', { name: 'Tarefas de hoje', hidden: true }),
    ).toBeInTheDocument()
  })
})

describe('Contador da aba (RN-63)', () => {
  it('atrasadas + hoje, em vermelho; oculto com 0', async () => {
    const { unmount } = comHoje({ atrasadas, hoje: [tarefaHoje({ id: 'h1' })] }, '/')

    const aba = await screen.findByRole('link', { name: /^Tarefas de hoje/ })
    await waitFor(() => expect(aba).toHaveTextContent('Tarefas de hoje3'))
    expect(within(aba).getByText('3')).toHaveClass('bg-red-600')

    unmount()
    comHoje({}, '/')
    // As consultas simuladas já responderam quando a home mostra o estado vazio.
    expect(await screen.findByText('Crie seu primeiro projeto')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tarefas de hoje' })).toHaveTextContent(
      /^Tarefas de hoje$/,
    )
  })
})
