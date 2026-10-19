/** Os 6 fluxos de 07 §5, no app de verdade (build + back-end), com hoje = 14/10/2026. */
import {
  arrastar,
  card,
  coluna,
  criarProjeto,
  escolherDia,
  expect,
  nomeUnico,
  test,
} from './ajuda.ts'

test('1. projeto e tarefa rápida: arrastar até Concluída atualiza o progresso', async ({
  page,
}) => {
  await criarProjeto(page, nomeUnico('Reforma'), { progresso: true })
  const progresso = page.getByText(/^(Sem tarefas|\d+\/\d+ tarefas)$/).first()
  await expect(progresso).toHaveText('Sem tarefas')

  const campo = page.getByRole('textbox', { name: 'Nova tarefa' })
  await campo.fill('Comprar tinta')
  await campo.press('Enter')
  await expect(card(coluna(page, 'Pendente'), 'Comprar tinta')).toBeVisible()
  await expect(progresso).toHaveText('0/1 tarefas')

  await arrastar(page, card(page, 'Comprar tinta'), coluna(page, 'Em andamento'))
  await expect(card(coluna(page, 'Em andamento'), 'Comprar tinta')).toBeVisible()

  await arrastar(page, card(page, 'Comprar tinta'), coluna(page, 'Concluída'))
  await expect(card(coluna(page, 'Concluída'), 'Comprar tinta')).toBeVisible()
  await expect(progresso).toHaveText('1/1 tarefas')
})

test('2. lembrete vencendo em 2 dias: aviso ao recarregar; dar baixa some; desfazer volta', async ({
  page,
}) => {
  await criarProjeto(page, nomeUnico('Casa'))
  const titulo = nomeUnico('Pagar IPTU')
  await page.getByRole('button', { name: 'Lembrete', exact: true }).click()
  const modal = page.getByRole('dialog', { name: 'Novo lembrete' })
  await modal.getByLabel('Título *').fill(titulo)
  await escolherDia(modal, 'Vencimento *', 16)
  await modal.getByRole('button', { name: 'Salvar' }).click()
  await expect(modal).toBeHidden()

  await page.reload()
  const painel = page.getByRole('region', { name: 'Avisos' })
  const aviso = painel.getByRole('listitem').filter({ hasText: titulo })
  // Painel carregado; se os outros fluxos deixaram mais de 3 avisos, este pode estar no "Ver mais".
  await expect(painel.getByRole('listitem').first()).toBeVisible()
  const verMais = painel.getByRole('button', { name: /Ver mais/ })
  if ((await verMais.count()) > 0) await verMais.click()
  await expect(aviso).toContainText('vence em 2 dias')

  await aviso.getByRole('button', { name: 'Dar baixa' }).click()
  await expect(page.getByText('Baixa registrada')).toBeVisible()
  await expect(page.getByRole('listitem').filter({ hasText: titulo })).toHaveCount(0)

  await page.getByRole('button', { name: 'Desfazer' }).click()
  await expect(page.getByRole('region', { name: 'Avisos' }).getByText(titulo)).toBeVisible()
})

test('3. tarefa repetida semanal: concluir avança o prazo uma semana', async ({ page }) => {
  await criarProjeto(page, nomeUnico('Jardim'))
  await page.getByRole('button', { name: 'Mais opções' }).click()
  const modal = page.getByRole('dialog', { name: 'Nova tarefa' })
  await modal.getByPlaceholder('Título da tarefa').fill('Regar plantas')
  await modal.getByRole('combobox', { name: 'Tipo' }).click()
  await page.getByRole('option', { name: 'Repetida' }).click()
  await escolherDia(modal, 'Primeira data *', 14)
  await modal.getByRole('combobox', { name: 'Unidade' }).click()
  await page.getByRole('option', { name: 'semanas' }).click()
  // A quarta (dia da primeira data) já vem marcada.
  await expect(modal.getByRole('button', { name: 'quarta' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  await modal.getByRole('button', { name: 'Salvar' }).click()
  await expect(modal).toBeHidden()

  const tarefa = card(coluna(page, 'Pendente'), 'Regar plantas')
  await expect(tarefa).toContainText('14/10')
  await tarefa.click()
  await page.getByRole('dialog').getByRole('button', { name: 'Concluir' }).click()
  await expect(page.getByText('Tarefa concluída')).toBeVisible()
  await expect(card(coluna(page, 'Pendente'), 'Regar plantas')).toContainText('21/10')
})

test('4. meta mensal de 2 vezes: +1, +1 vai para Concluída', async ({ page }) => {
  await criarProjeto(page, nomeUnico('Saúde'))
  await page.getByRole('button', { name: 'Mais opções' }).click()
  const modal = page.getByRole('dialog', { name: 'Nova tarefa' })
  await modal.getByPlaceholder('Título da tarefa').fill('Correr')
  await modal.getByRole('combobox', { name: 'Tipo' }).click()
  await page.getByRole('option', { name: 'Meta mensal' }).click()
  await modal.getByLabel('Quantas vezes por mês *').fill('2')
  await modal.getByRole('button', { name: 'Salvar' }).click()
  await expect(modal).toBeHidden()

  const maisUm = page.getByRole('button', { name: '+1 em Correr' })
  await maisUm.click()
  await expect(card(coluna(page, 'Pendente'), 'Correr')).toContainText('meta 1/2')
  await maisUm.click()
  await expect(card(coluna(page, 'Concluída'), 'Correr')).toContainText('meta 2/2')
})

test('5. PDF: enviar, abrir, renomear, excluir e restaurar da lixeira', async ({ page }) => {
  const endereco = await criarProjeto(page, nomeUnico('Obra'))
  await page.getByLabel('Arquivos para enviar').setInputFiles({
    name: 'Contrato.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4\n%%EOF\n'),
  })
  const link = page.getByRole('link', { name: 'Contrato.pdf' })
  await expect(link).toBeVisible()

  // Abrir: PDF abre numa aba nova e a API manda `inline` (RN-71).
  await expect(link).toHaveAttribute('target', '_blank')
  const arquivo = await page.request.get((await link.getAttribute('href')) ?? '')
  expect(arquivo.ok()).toBe(true)
  expect(arquivo.headers()['content-disposition']).toMatch(/^inline;/)

  await page.getByRole('button', { name: 'Ações de Contrato.pdf' }).click()
  await page.getByRole('menuitem', { name: 'Renomear' }).click()
  const dialogo = page.getByRole('dialog', { name: 'Renomear documento' })
  await dialogo.getByLabel('Nome').fill('Contrato assinado')
  await dialogo.getByRole('button', { name: 'Salvar' }).click()
  // RN-72: a extensão original é mantida.
  await expect(page.getByRole('link', { name: 'Contrato assinado.pdf' })).toBeVisible()

  await page.getByRole('button', { name: 'Ações de Contrato assinado.pdf' }).click()
  await page.getByRole('menuitem', { name: 'Excluir' }).click()
  await expect(page.getByText('Movido para a lixeira')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Contrato assinado.pdf' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Menu' }).click()
  await page.getByRole('menuitem', { name: 'Lixeira' }).click()
  const linha = page.getByRole('listitem').filter({ hasText: 'Contrato assinado.pdf' })
  await linha.getByRole('button', { name: 'Restaurar' }).click()
  await expect(linha).toHaveCount(0)

  await page.goto(endereco)
  await expect(page.getByRole('link', { name: 'Contrato assinado.pdf' })).toBeVisible()
})

test('6. concluir projeto: some da home e reabre em Arquivados', async ({ page }) => {
  const nome = nomeUnico('Mudança')
  await criarProjeto(page, nome)
  await page.getByRole('button', { name: /Trocar status/ }).click()
  await page.getByRole('menuitemradio', { name: 'Concluído' }).click()

  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Projetos' })).toBeVisible()
  await expect(page.getByRole('link', { name: nome, exact: true })).toHaveCount(0)

  await page.getByRole('button', { name: 'Menu' }).click()
  await page.getByRole('menuitem', { name: 'Arquivados' }).click()
  await page.getByRole('button', { name: `Reabrir ${nome}` }).click()
  await expect(page.getByRole('button', { name: `Reabrir ${nome}` })).toHaveCount(0)

  await page.goto('/')
  await expect(page.getByRole('link', { name: nome, exact: true })).toBeVisible()
})
