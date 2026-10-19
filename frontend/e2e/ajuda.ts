import { expect, type Locator, type Page, test as base } from '@playwright/test'
import { HOJE } from './constantes.ts'

/** `page` com o relógio do navegador no mesmo "hoje" do servidor (o calendário abre no mês certo). */
export const test = base.extend({
  // `entregar` (e não `use`, o nome da documentação): o lint de hooks do React não confunde.
  page: async ({ page }, entregar) => {
    await page.clock.setFixedTime(new Date(`${HOJE}T12:00:00-03:00`))
    await entregar(page)
  },
})

export { expect }

/** O banco vive a execução inteira: cada fluxo usa nomes próprios. */
export function nomeUnico(base: string) {
  return `${base} ${Math.random().toString(36).slice(2, 6)}`
}

/** Cria pela home e abre o projeto; devolve o endereço dele. */
export async function criarProjeto(page: Page, nome: string, opcoes: { progresso?: boolean } = {}) {
  await page.goto('/')
  await page.getByRole('button', { name: 'Novo projeto' }).first().click()
  const modal = page.getByRole('dialog', { name: 'Novo projeto' })
  await modal.getByLabel('Nome *').fill(nome)
  if (opcoes.progresso) await modal.getByRole('switch', { name: 'Acompanhar progresso' }).click()
  await modal.getByRole('button', { name: 'Salvar' }).click()
  await expect(modal).toBeHidden()
  await page.getByRole('link', { name: nome, exact: true }).click()
  await expect(page.getByRole('heading', { name: nome })).toBeVisible()
  return page.url()
}

/** Escolhe um dia de outubro de 2026 no calendário do campo de data com este rótulo. */
export async function escolherDia(dentro: Locator, rotulo: string, dia: number) {
  await dentro.getByLabel(rotulo).click()
  await dentro
    .page()
    .getByRole('button', { name: new RegExp(`(^|\\D)${dia} de outubro de 2026`) })
    .click()
}

/** Arrasta com o mouse (dnd-kit só começa depois de 5 px). */
export async function arrastar(page: Page, item: Locator, destino: Locator) {
  const de = await item.boundingBox()
  const para = await destino.boundingBox()
  if (!de || !para) throw new Error('Item ou destino fora da tela')
  const x = de.x + de.width / 2
  const y = de.y + de.height / 2
  await page.mouse.move(x, y)
  await page.mouse.down()
  await page.mouse.move(x + 10, y, { steps: 5 })
  await page.mouse.move(para.x + para.width / 2, para.y + 60, { steps: 20 })
  await page.mouse.up()
}

export const coluna = (page: Page, nome: 'Pendente' | 'Em andamento' | 'Concluída') =>
  page.getByRole('region', { name: nome, exact: true })

/** O card arrastável da tarefa (nome = título; não pega os botões "+1 em …"). */
export const card = (dentro: Locator | Page, titulo: string) =>
  dentro.getByRole('button', { name: titulo, exact: true })
