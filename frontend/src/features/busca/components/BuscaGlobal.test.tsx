import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderizarRota, simularGet } from '@/test/renderizar'

const PROJETO = { id: '11111111-1111-4111-8111-111111111111', nome: 'Reforma', cor: 'azul' }
const ARQUIVADO = { id: 'p2', nome: 'Mudança', cor: 'verde' }

const item = (id: string, titulo: string, projeto = PROJETO, arquivado = false) => ({
  id,
  titulo,
  projeto,
  arquivado,
})

const VAZIO = { projetos: [], tarefas: [], lembretes: [], anotacoes: [], documentos: [] }

function comBusca(resultado: Partial<typeof VAZIO> | Record<string, unknown> = {}) {
  const get = simularGet({ '/api/busca': { ...VAZIO, ...resultado } })
  renderizarRota('/')
  return { usuario: userEvent.setup(), get }
}

const chamadasDaBusca = (get: ReturnType<typeof simularGet>) =>
  get.mock.calls.filter((chamada) => chamada[0] === '/api/busca')

describe('BuscaGlobal (01 §3, RN-120..121)', () => {
  it('Ctrl+K abre; com menos de 2 letras só mostra a dica, sem chamar a API', async () => {
    const { usuario, get } = comBusca()
    await screen.findByRole('button', { name: /Buscar/ })

    await usuario.keyboard('{Control>}k{/Control}')

    const dialogo = within(await screen.findByRole('dialog', { name: 'Buscar' }))
    expect(dialogo.getByRole('searchbox', { name: 'Buscar' })).toHaveFocus()
    await usuario.type(dialogo.getByRole('searchbox'), 'c')
    expect(dialogo.getByText('Digite pelo menos 2 letras.')).toBeInTheDocument()
    expect(chamadasDaBusca(get)).toHaveLength(0)
  })

  it('mostra os resultados por tipo, com projeto, "Arquivado" e o destino certo', async () => {
    const { usuario, get } = comBusca({
      projetos: [item(PROJETO.id, 'Reforma')],
      tarefas: [item('t1', 'Azulejo da cozinha'), item('t2', 'Caixas', ARQUIVADO, true)],
      lembretes: [item('l1', 'Gás')],
      anotacoes: [item('n1', 'Medidas da cozinha')],
      documentos: [item('d1', 'Planta.pdf')],
    })

    await usuario.click(await screen.findByRole('button', { name: /Buscar/ }))
    await usuario.type(screen.getByRole('searchbox', { name: 'Buscar' }), 'cozinha')

    const dialogo = within(await screen.findByRole('dialog', { name: 'Buscar' }))
    const tarefas = within(await dialogo.findByRole('region', { name: 'Tarefas' }))
    expect(chamadasDaBusca(get).at(-1)).toEqual([
      '/api/busca',
      { params: { query: { q: 'cozinha' } } },
    ])

    const azulejo = tarefas.getByRole('link', { name: /Azulejo da cozinha/ })
    expect(azulejo).toHaveAttribute('href', `/projetos/${PROJETO.id}?tarefa=t1`)
    expect(within(azulejo).getByText('Reforma')).toBeInTheDocument()
    const caixas = tarefas.getByRole('link', { name: /Caixas/ })
    expect(within(caixas).getByText('Arquivado')).toBeInTheDocument()
    expect(within(azulejo).queryByText('Arquivado')).not.toBeInTheDocument()

    const projetos = within(dialogo.getByRole('region', { name: 'Projetos' }))
    expect(projetos.getByRole('link', { name: 'Reforma' })).toHaveAttribute(
      'href',
      `/projetos/${PROJETO.id}`,
    )
    for (const [grupo, titulo] of [
      ['Lembretes', /Gás/],
      ['Anotações', /Medidas da cozinha/],
      ['Documentos', /Planta.pdf/],
    ] as const) {
      const link = within(dialogo.getByRole('region', { name: grupo })).getByRole('link', {
        name: titulo,
      })
      expect(link).toHaveAttribute('href', `/projetos/${PROJETO.id}`)
    }
  })

  it('sem resultados: "Nada encontrado para …"', async () => {
    const { usuario } = comBusca()

    await usuario.click(await screen.findByRole('button', { name: /Buscar/ }))
    await usuario.type(screen.getByRole('searchbox', { name: 'Buscar' }), 'xyz')

    expect(await screen.findByText('Nada encontrado para “xyz”.')).toBeInTheDocument()
  })

  it('clicar num resultado fecha a busca e abre o projeto', async () => {
    const { usuario } = comBusca({ projetos: [item(PROJETO.id, 'Reforma')] })

    await usuario.click(await screen.findByRole('button', { name: /Buscar/ }))
    await usuario.type(screen.getByRole('searchbox', { name: 'Buscar' }), 'refor')
    await usuario.click(await screen.findByRole('link', { name: 'Reforma' }))

    await waitFor(() =>
      expect(screen.queryByRole('dialog', { name: 'Buscar' })).not.toBeInTheDocument(),
    )
    expect(await screen.findByRole('heading', { name: 'Reforma' })).toBeInTheDocument()
  })
})
