import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import {
  aviso,
  avisos,
  lembrete,
  renderizarRota,
  saude,
  simularEscrita,
  simularGet,
  sucesso,
  tarefa,
} from '@/test/renderizar'

const PROJETO = '11111111-1111-4111-8111-111111111111'

const painel = () => within(screen.getByRole('region', { name: 'Avisos' }))
const itemDe = (titulo: string) => within(painel().getByText(titulo).closest('li')!)

function comAvisos(...itens: ReturnType<typeof aviso>[]) {
  const get = simularGet({ '/api/avisos': avisos(...itens) })
  renderizarRota('/')
  return { usuario: userEvent.setup(), get }
}

const cinco = ['A', 'B', 'C', 'D', 'E'].map((titulo) => aviso({ id: titulo, titulo }))

describe('PainelAvisos (01 §4.1, RN-52..55)', () => {
  it('mostra os 3 primeiros e "Ver mais N" expande a lista toda (RN-52)', async () => {
    const { usuario } = comAvisos(...cinco)

    expect(await screen.findByRole('region', { name: 'Avisos' })).toBeInTheDocument()
    expect(painel().getByLabelText('5 no total')).toHaveTextContent('5')
    const titulos = () =>
      painel()
        .getAllByRole('listitem')
        .map((li) => within(li).getByText(/^[A-E]$/).textContent)
    expect(titulos()).toEqual(['A', 'B', 'C'])

    await usuario.click(painel().getByRole('button', { name: 'Ver mais 2' }))

    expect(painel().getAllByRole('listitem')).toHaveLength(5)
    expect(painel().queryByRole('button', { name: /Ver mais/ })).not.toBeInTheDocument()
  })

  it('sem avisos não aparece; o sino fica sem contador (RN-55)', async () => {
    comAvisos()

    expect(await screen.findByRole('button', { name: 'Avisos' })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Avisos' })).not.toBeInTheDocument()
  })

  it('Fechar oculta o painel; o sino mostra o total e reabre (RN-52, RN-55)', async () => {
    const { usuario } = comAvisos(...cinco.slice(0, 2))

    await usuario.click(await screen.findByRole('button', { name: 'Fechar avisos' }))

    expect(screen.queryByRole('region', { name: 'Avisos' })).not.toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Avisos: 2' }))
    expect(screen.getByRole('region', { name: 'Avisos' })).toBeInTheDocument()
  })

  it('cada aviso: tipo, projeto, data, texto de prazo com cor, urgência, ocorrências e meta', async () => {
    comAvisos(
      aviso({ id: 'v', titulo: 'Vencido', dias_restantes: -3, ocorrencias_atrasadas: 3 }),
      aviso({ id: 'u', titulo: 'Uma perdida', dias_restantes: -1, ocorrencias_atrasadas: 1 }),
      aviso({ tipo: 'tarefa', id: 'h', titulo: 'Hoje', dias_restantes: 0 }),
      aviso({
        tipo: 'tarefa',
        id: 'm',
        titulo: 'Correr',
        dias_restantes: 2,
        meta: { feitas: 2, meta: 4 },
      }),
      aviso({ id: 'f', titulo: 'Futuro', dias_restantes: 3 }),
    )
    await screen.findByRole('region', { name: 'Avisos' })
    await userEvent.setup().click(painel().getByRole('button', { name: 'Ver mais 2' }))

    const linha = (titulo: string) => painel().getByText(titulo).closest('li')!

    const vencido = itemDe('Vencido')
    expect(vencido.getByText('Lembrete')).toBeInTheDocument()
    expect(vencido.getByText('Projeto')).toBeInTheDocument()
    expect(vencido.getByText('Reforma')).toBeInTheDocument()
    // Vencimento do lembrete (17/10, no ano corrente da API: só dia e mês).
    expect(vencido.getByText('Vencimento')).toBeInTheDocument()
    expect(vencido.getByText('17/10')).toBeInTheDocument()
    expect(vencido.getByText('vencido há 3 dias · 3 ocorrências')).toHaveClass('text-red-600')
    expect(linha('Vencido')).toHaveClass('border-l-red-500')
    expect(itemDe('Uma perdida').getByText('vencido há 1 dia')).toBeInTheDocument()

    const hoje = itemDe('Hoje')
    expect(hoje.getByText('Tarefa')).toBeInTheDocument()
    expect(hoje.getByText('Prazo')).toBeInTheDocument()
    expect(hoje.getByText('vence hoje')).toHaveClass('text-amber-600')
    expect(linha('Hoje')).toHaveClass('border-l-amber-500')
    expect(hoje.getByRole('button', { name: 'Concluir' })).toBeInTheDocument()

    const meta = itemDe('Correr')
    expect(meta.getByText('Meta mensal')).toBeInTheDocument()
    expect(meta.getByText('2/4 no mês')).toBeInTheDocument()
    expect(meta.getByText('mês termina em 2 dias')).toHaveClass('text-muted-foreground')
    expect(meta.getByRole('button', { name: '+1' })).toBeInTheDocument()

    expect(itemDe('Futuro').getByText('vence em 3 dias')).toHaveClass('text-muted-foreground')
    expect(linha('Futuro')).toHaveClass('border-l-sky-400')
  })

  it('Abrir projeto e Abrir levam ao projeto e ao modal da tarefa', async () => {
    comAvisos(
      aviso({ id: 'l1', titulo: 'IPTU' }),
      aviso({ tipo: 'tarefa', id: 't1', titulo: 'Pintar' }),
    )
    await screen.findByRole('region', { name: 'Avisos' })

    expect(itemDe('IPTU').getByRole('link', { name: 'Abrir projeto' })).toHaveAttribute(
      'href',
      `/projetos/${PROJETO}`,
    )
    expect(itemDe('Pintar').getByRole('link', { name: 'Abrir' })).toHaveAttribute(
      'href',
      `/projetos/${PROJETO}?tarefa=t1`,
    )
  })
})

describe('Ações no painel (RN-54)', () => {
  it('Dar baixa tira o item do painel e do sino; Desfazer chama desfazer-baixa e devolve', async () => {
    const { usuario } = comAvisos(
      aviso({ id: 'l1', titulo: 'IPTU' }),
      aviso({ id: 'l2', titulo: 'Luz' }),
    )
    const post = simularEscrita('POST', sucesso(lembrete()))

    await usuario.click(
      within((await screen.findByText('IPTU')).closest('li')!).getByRole('button', {
        name: 'Dar baixa',
      }),
    )

    expect(await screen.findByText('Baixa registrada')).toBeInTheDocument()
    expect(post).toHaveBeenCalledWith('/api/lembretes/{lembrete_id}/baixa', {
      params: { path: { lembrete_id: 'l1' } },
    })
    // A API ainda devolve o item (simulação fixa), mas o painel o tira até o próximo acesso.
    expect(painel().queryByText('IPTU')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Avisos: 1' })).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/lembretes/{lembrete_id}/desfazer-baixa', {
        params: { path: { lembrete_id: 'l1' } },
      }),
    )
    expect(await painel().findByText('IPTU')).toBeInTheDocument()
  })

  it('Concluir (tarefa) e +1 (meta) chamam concluir; Desfazer chama desfazer-conclusao', async () => {
    const { usuario } = comAvisos(
      aviso({ tipo: 'tarefa', id: 't1', titulo: 'Pintar' }),
      aviso({ tipo: 'tarefa', id: 'm1', titulo: 'Correr', meta: { feitas: 2, meta: 4 } }),
    )
    const post = simularEscrita('POST', sucesso(tarefa()))

    await usuario.click(
      within((await screen.findByText('Correr')).closest('li')!).getByRole('button', {
        name: '+1',
      }),
    )

    expect(await screen.findByText('+1 registrado')).toBeInTheDocument()
    expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/concluir', {
      params: { path: { tarefa_id: 'm1' } },
    })
    expect(painel().queryByText('Correr')).not.toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/desfazer-conclusao', {
        params: { path: { tarefa_id: 'm1' } },
      }),
    )

    await usuario.click(itemDe('Pintar').getByRole('button', { name: 'Concluir' }))

    expect(await screen.findByText('Tarefa concluída')).toBeInTheDocument()
    expect(post).toHaveBeenCalledWith('/api/tarefas/{tarefa_id}/concluir', {
      params: { path: { tarefa_id: 't1' } },
    })
  })

  it('o último item tratado fecha o painel; erro da API mostra a mensagem e mantém o item', async () => {
    const { usuario } = comAvisos(aviso({ id: 'l1', titulo: 'IPTU' }))
    simularEscrita('POST', {
      error: { erro: { codigo: 'conflito', mensagem: 'Já tem baixa.', campos: null } },
      response: new Response(null, { status: 409 }),
    })

    await usuario.click(await screen.findByRole('button', { name: 'Dar baixa' }))

    expect(await screen.findByText('Já tem baixa.')).toBeInTheDocument()
    expect(painel().getByText('IPTU')).toBeInTheDocument()

    simularEscrita('POST', sucesso(lembrete()))
    await usuario.click(painel().getByRole('button', { name: 'Dar baixa' }))

    await waitFor(() =>
      expect(screen.queryByRole('region', { name: 'Avisos' })).not.toBeInTheDocument(),
    )
  })
})

describe('Novo dia (RN-53)', () => {
  it('ao voltar o foco com outro "hoje", busca os avisos de novo e reabre o painel', async () => {
    const { usuario, get } = comAvisos(aviso({ id: 'l1', titulo: 'IPTU' }))
    await usuario.click(await screen.findByRole('button', { name: 'Fechar avisos' }))

    // Mesmo dia: continua fechado.
    const buscasDaSaude = () => get.mock.calls.filter((chamada) => chamada[0] === '/api/saude')
    fireEvent.focus(window)
    await waitFor(() => expect(buscasDaSaude()).toHaveLength(2))
    expect(screen.queryByRole('region', { name: 'Avisos' })).not.toBeInTheDocument()

    simularGet({
      '/api/saude': saude({ hoje: '2026-10-15' }),
      '/api/avisos': avisos(
        aviso({ id: 'l1', titulo: 'IPTU' }),
        aviso({ id: 'l2', titulo: 'Luz' }),
      ),
    })
    fireEvent(document, new Event('visibilitychange'))

    expect(await screen.findByRole('region', { name: 'Avisos' })).toBeInTheDocument()
    expect(await painel().findByText('Luz')).toBeInTheDocument()
  })
})
