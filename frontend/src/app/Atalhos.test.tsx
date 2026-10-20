import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button } from '@/components/ui/button'
import { aviso, avisos, renderizarRota, simularGet } from '@/test/renderizar'

const PROJETO = '/projetos/11111111-1111-4111-8111-111111111111'

describe('Atalhos (RN-130)', () => {
  it('"/" abre a busca; digitado num campo de texto, é só um caractere', async () => {
    simularGet()
    renderizarRota(PROJETO)
    const usuario = userEvent.setup()
    const campo = await screen.findByRole('textbox', { name: 'Nova tarefa' })

    await usuario.type(campo, 'a/b')
    expect(campo).toHaveValue('a/b')
    expect(screen.queryByRole('dialog', { name: 'Buscar' })).not.toBeInTheDocument()

    await usuario.click(document.body)
    await usuario.keyboard('/')
    const busca = await screen.findByRole('searchbox', { name: 'Buscar' })
    // O "/" abre a busca e não aparece digitado nela.
    expect(busca).toHaveValue('')
  })

  it('"N" foca a criação rápida no projeto; com um modal aberto, não', async () => {
    simularGet()
    renderizarRota(PROJETO)
    const usuario = userEvent.setup()
    const campo = await screen.findByRole('textbox', { name: 'Nova tarefa' })

    await usuario.keyboard('n')
    expect(campo).toHaveFocus()
    expect(campo).toHaveValue('')

    await usuario.click(screen.getByRole('button', { name: 'Nova tarefa' }))
    await screen.findByRole('dialog')
    await usuario.click(screen.getByRole('dialog'))
    await usuario.keyboard('n')
    expect(campo).not.toHaveFocus()
  })

  it('"Esc" fecha o painel de avisos; com um modal aberto, fecha só o modal', async () => {
    simularGet({ '/api/avisos': avisos(aviso({ titulo: 'IPTU' })) })
    renderizarRota(PROJETO)
    const usuario = userEvent.setup()
    await screen.findByRole('region', { name: 'Avisos' })

    await usuario.click(await screen.findByRole('button', { name: 'Nova tarefa' }))
    await screen.findByRole('dialog')
    await usuario.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(screen.getByRole('region', { name: 'Avisos' })).toBeInTheDocument()

    await usuario.keyboard('{Escape}')
    await waitFor(() =>
      expect(screen.queryByRole('region', { name: 'Avisos' })).not.toBeInTheDocument(),
    )
  })
})

describe('Estados de erro e carregando (05 §9)', () => {
  it('endereço desconhecido: "Página não encontrada." com volta para Projetos', async () => {
    simularGet()
    renderizarRota('/nao-existe')

    expect(await screen.findByText('Página não encontrada.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Voltar para Projetos' })).toHaveAttribute('href', '/')
  })

  it('erro inesperado numa tela: "Algo deu errado." com Recarregar', async () => {
    // Resposta fora do contrato faz a tela quebrar ao renderizar.
    simularGet({ '/api/projetos': null })
    vi.spyOn(console, 'error').mockImplementation(() => {})
    renderizarRota('/')

    expect(await screen.findByText('Algo deu errado.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Recarregar' })).toBeEnabled()
  })

  it('botão carregando: indicador, inativo e aria-busy', () => {
    const { rerender } = render(<Button carregando>Salvar</Button>)

    const botao = screen.getByRole('button', { name: 'Salvar' })
    expect(botao).toBeDisabled()
    expect(botao).toHaveAttribute('aria-busy', 'true')
    expect(within(botao).getByText('Salvar')).toBeInTheDocument()
    expect(botao.querySelector('.animate-spin')).not.toBeNull()

    rerender(<Button>Salvar</Button>)
    expect(botao).toBeEnabled()
    expect(botao).not.toHaveAttribute('aria-busy')
    expect(botao.querySelector('.animate-spin')).toBeNull()
  })
})
