import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import {
  quadro,
  renderizarRota,
  simularEscrita,
  simularGet,
  sucesso,
  tarefa,
} from '@/test/renderizar'
import type { Recorrencia } from '@/lib/recorrencia'

const ID = '11111111-1111-4111-8111-111111111111'
const URL = `/projetos/${ID}`
const SEGUNDA: Recorrencia = {
  frequencia: 'semanal',
  intervalo: 1,
  dias_semana: [0],
  dia_mes: null,
  mes: null,
}

async function escolher(
  usuario: ReturnType<typeof userEvent.setup>,
  rotulo: string,
  opcao: string,
) {
  await usuario.click(screen.getByRole('combobox', { name: rotulo }))
  await usuario.click(await screen.findByRole('option', { name: opcao }))
}

function abrirEdicao(dados: Parameters<typeof tarefa>[0], execucoes: { data: string }[] = []) {
  const existente = tarefa({ id: 't1', ...dados })
  simularGet({
    '/api/tarefas/{tarefa_id}': {
      ...existente,
      execucoes: execucoes.map((e) => ({ ...e, criado_em: `${e.data}T15:00:00Z` })),
    },
  })
  renderizarRota(`${URL}?tarefa=t1`)
  return { existente, usuario: userEvent.setup() }
}

describe('Modal da tarefa: campos por tipo (01 §4.6)', () => {
  it('meta mensal pede "Quantas vezes por mês" e não tem prazo', async () => {
    simularGet()
    const post = simularEscrita('POST', sucesso(tarefa(), 201))
    const usuario = userEvent.setup()
    renderizarRota(URL)
    await usuario.click(await screen.findByRole('button', { name: 'Nova tarefa' }))
    await usuario.type(await screen.findByLabelText('Título'), 'Correr')

    await escolher(usuario, 'Tipo', 'Meta mensal')
    expect(screen.queryByLabelText('Prazo')).not.toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))
    expect(await screen.findByText('Informe quantas vezes por mês (1 a 31).')).toBeInTheDocument()
    await usuario.type(screen.getByLabelText('Quantas vezes por mês *'), '4')
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/projetos/{projeto_id}/tarefas', {
        params: { path: { projeto_id: ID } },
        body: {
          titulo: 'Correr',
          descricao: '',
          prioridade: 'media',
          tipo: 'meta_mensal',
          prazo: null,
          recorrencia: null,
          meta_mensal: 4,
        },
      }),
    )
  })

  it('repetida exige a primeira data e mostra o editor com a frase de RN-35', async () => {
    simularGet()
    const post = simularEscrita('POST', sucesso(tarefa(), 201))
    const usuario = userEvent.setup()
    renderizarRota(URL)
    await usuario.click(await screen.findByRole('button', { name: 'Nova tarefa' }))
    await usuario.type(await screen.findByLabelText('Título'), 'Regar')

    await escolher(usuario, 'Tipo', 'Repetida')
    expect(screen.getByLabelText('Primeira data *')).toBeInTheDocument()
    expect(screen.getByText('Repete todo dia')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))

    expect(await screen.findByText('Informe a primeira data.')).toBeInTheDocument()
    expect(post).not.toHaveBeenCalled()
  })

  it('simples → repetida: semanas marca o dia da data e o PATCH leva a regra de RN-30', async () => {
    // 14/10/2026 é quarta.
    const { usuario } = abrirEdicao({ prazo: '2026-10-14' })
    const patch = simularEscrita('PATCH', sucesso(tarefa()))
    await screen.findByLabelText('Título')

    await escolher(usuario, 'Tipo', 'Repetida')
    expect(screen.getByLabelText('Próxima data *')).toHaveTextContent('14/10/2026')
    await escolher(usuario, 'Unidade', 'semanas')
    const dias = within(screen.getByRole('group', { name: 'Dias da semana' }))
    expect(dias.getByRole('button', { name: 'quarta' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Repete toda quarta')).toBeInTheDocument()
    await usuario.click(dias.getByRole('button', { name: 'segunda' }))
    expect(screen.getByText('Repete toda semana: segunda e quarta')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}', {
        params: { path: { tarefa_id: 't1' } },
        body: {
          tipo: 'repetida',
          prazo: '2026-10-14',
          recorrencia: { ...SEGUNDA, dias_semana: [0, 2] },
          meta_mensal: null,
        },
      }),
    )
  })

  it('repetida: mostra "Próxima" com a regra e as últimas conclusões; voltar a simples limpa a regra', async () => {
    const { usuario } = abrirEdicao(
      {
        tipo: 'repetida',
        prazo: '2026-10-19',
        recorrencia: SEGUNDA,
        recorrencia_descricao: 'toda segunda',
      },
      [{ data: '2026-10-12' }, { data: '2026-10-05' }],
    )
    const patch = simularEscrita('PATCH', sucesso(tarefa()))

    expect(await screen.findByText('Próxima: 19/10/2026 · toda segunda')).toBeInTheDocument()
    expect(screen.getByText('Últimas conclusões: 12/10/2026, 05/10/2026')).toBeInTheDocument()
    const dias = within(screen.getByRole('group', { name: 'Dias da semana' }))
    expect(dias.getByRole('button', { name: 'segunda' })).toHaveAttribute('aria-pressed', 'true')

    await escolher(usuario, 'Tipo', 'Simples')
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}', {
        params: { path: { tarefa_id: 't1' } },
        body: { tipo: 'simples', prazo: '2026-10-19', recorrencia: null, meta_mensal: null },
      }),
    )
  })

  it('meta: "2 de 4 neste mês", sem status, e +1 deixa o modal aberto', async () => {
    const { usuario } = abrirEdicao({ tipo: 'meta_mensal', meta_mensal: 4, progresso_mes: 2 }, [
      { data: '2026-10-05' },
      { data: '2026-10-02' },
    ])
    const post = simularEscrita('POST', sucesso(tarefa({ progresso_mes: 3 })))

    expect(await screen.findByText('2 de 4 neste mês')).toBeInTheDocument()
    expect(screen.getByText('Feitas em: 05/10/2026, 02/10/2026')).toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: 'Status' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Concluir' })).not.toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: '+1' }))

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/concluir', {
        params: { path: { tarefa_id: 't1' } },
      }),
    )
    expect(screen.getByRole('dialog', { name: 'Tarefa' })).toBeInTheDocument()
  })
})

describe('Card do quadro: selos e +1/−1 (01 §4.4)', () => {
  it('mostra "repete" e "meta 2/4"; +1 e −1 salvam sem abrir o modal', async () => {
    simularGet({
      '/api/projetos/{projeto_id}/tarefas': quadro({
        pendente: [
          tarefa({
            id: 'r',
            titulo: 'Regar',
            tipo: 'repetida',
            prazo: '2026-10-19',
            recorrencia: SEGUNDA,
          }),
          tarefa({
            id: 'm',
            titulo: 'Correr',
            tipo: 'meta_mensal',
            meta_mensal: 4,
            progresso_mes: 2,
          }),
          tarefa({ id: 'z', titulo: 'Ler', tipo: 'meta_mensal', meta_mensal: 3, progresso_mes: 0 }),
        ],
      }),
    })
    const post = simularEscrita('POST', sucesso(tarefa()))
    const usuario = userEvent.setup()
    renderizarRota(URL)

    const card = async (titulo: string) =>
      within((await screen.findByText(titulo)).closest('article')!)
    expect((await card('Regar')).getByText('repete')).toBeInTheDocument()
    expect((await card('Correr')).getByText('meta 2/4')).toBeInTheDocument()
    expect((await card('Ler')).getByRole('button', { name: '−1 em Ler' })).toBeDisabled()

    await usuario.click((await card('Correr')).getByRole('button', { name: '+1 em Correr' }))
    await usuario.click((await card('Correr')).getByRole('button', { name: '−1 em Correr' }))

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/concluir', {
        params: { path: { tarefa_id: 'm' } },
      }),
    )
    expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/execucoes/remover-ultima', {
      params: { path: { tarefa_id: 'm' } },
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
