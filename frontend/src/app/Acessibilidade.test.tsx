import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import {
  anotacao,
  aviso,
  avisos,
  documento,
  itemLixeira,
  lembrete,
  projeto,
  quadro,
  renderizarRota,
  simularGet,
  tarefa,
  tarefaHoje,
} from '@/test/renderizar'

const ID = '11111111-1111-4111-8111-111111111111'

const PAPEIS = ['button', 'link', 'checkbox', 'switch', 'textbox', 'searchbox', 'radio'] as const

/** 05 §9: todo controle (inclusive os só com ícone) tem nome para leitor de tela. */
function todosOsControlesTemNome() {
  for (const papel of PAPEIS) {
    for (const controle of screen.queryAllByRole(papel)) {
      expect(
        controle,
        `${papel} sem nome: ${controle.outerHTML.slice(0, 120)}`,
      ).toHaveAccessibleName()
    }
  }
}

function comDados() {
  simularGet({
    '/api/avisos': avisos(
      aviso({ titulo: 'IPTU' }),
      aviso({ tipo: 'tarefa', id: 't9', titulo: 'Pintar' }),
    ),
    '/api/projetos': [
      projeto({ acompanhar_progresso: true, progresso: { concluidas: 1, total: 2 }, avisos: 2 }),
    ],
    '/api/projetos/{projeto_id}/tarefas': quadro({
      pendente: [tarefa({ id: 't1', titulo: 'Comprar tinta', prioridade: 'alta' })],
      em_andamento: [
        tarefa({
          id: 't2',
          titulo: 'Correr',
          tipo: 'meta_mensal',
          meta_mensal: 4,
          progresso_mes: 1,
        }),
      ],
    }),
    '/api/projetos/{projeto_id}/lembretes': {
      ativos: [lembrete()],
      concluidos: [lembrete({ id: 'l2', concluido_em: '2026-10-10T12:00:00Z' })],
    },
    '/api/projetos/{projeto_id}/documentos': [documento()],
    '/api/projetos/{projeto_id}/anotacoes': [anotacao({ titulo: '' })],
    '/api/tarefas/hoje': {
      atrasadas: [tarefaHoje({ id: 'a1', titulo: 'Atrasada' })],
      hoje: [tarefaHoje({ id: 'h1', titulo: 'De hoje' })],
    },
    '/api/lixeira': [itemLixeira()],
  })
}

describe('Acessibilidade (05 §9)', () => {
  it.each([
    ['Projetos', '/', 'Reforma'],
    ['Tarefas de hoje', '/hoje', 'De hoje'],
    ['Projeto aberto', `/projetos/${ID}`, 'Comprar tinta'],
    ['Arquivados', '/arquivados', 'Arquivados'],
    ['Lixeira', '/lixeira', 'Comprar tinta'],
    ['Configurações', '/configuracoes', 'Backup'],
  ])('%s: todo controle tem nome acessível', async (_tela, url, texto) => {
    comDados()
    renderizarRota(url)

    expect((await screen.findAllByText(texto)).length).toBeGreaterThan(0)
    todosOsControlesTemNome()
  })

  it('teclado: Tab chega ao card da tarefa e Enter abre o modal dela', async () => {
    comDados()
    renderizarRota(`/projetos/${ID}`)
    const usuario = userEvent.setup()
    const card = (await screen.findByText('Comprar tinta')).closest('[role="button"]')
    expect(card).not.toBeNull()

    // Só teclado: Tab até o card (sem clicar nele).
    while (document.activeElement !== card) await usuario.tab()
    await usuario.keyboard('{Enter}')

    expect(await screen.findByRole('dialog')).toBeInTheDocument()
  })

  it('teclado: Tab chega ao card do projeto e Enter abre o projeto', async () => {
    comDados()
    renderizarRota('/')
    const usuario = userEvent.setup()
    const link = await screen.findByRole('link', { name: 'Reforma' })

    while (document.activeElement !== link) await usuario.tab()
    await usuario.keyboard('{Enter}')

    expect(await screen.findByRole('heading', { name: 'Reforma' })).toBeInTheDocument()
  })
})
