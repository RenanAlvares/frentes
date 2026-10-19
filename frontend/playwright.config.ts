import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { defineConfig, devices } from '@playwright/test'
import { HOJE, PORTA } from './e2e/constantes.ts'

// 07 §5: o app em modo de uso, com pasta de dados temporária (uma por execução; os
// workers recebem a mesma pelo ambiente).
process.env.FRENTES_E2E_DADOS ??= mkdtempSync(join(tmpdir(), 'frentes-e2e-'))

export default defineConfig({
  testDir: './e2e',
  // Um app e um banco só: os fluxos rodam um de cada vez.
  workers: 1,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: `http://127.0.0.1:${PORTA}`,
    locale: 'pt-BR',
    timezoneId: 'America/Sao_Paulo',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    // Build do front servido pelo back-end, como no uso local (06 §11).
    command: 'npm run build && uv run --directory ../backend frentes',
    url: `http://127.0.0.1:${PORTA}/api/saude`,
    reuseExistingServer: false,
    timeout: 240_000,
    stdout: 'ignore',
    stderr: 'pipe',
    env: {
      FRENTES_DATA_DIR: process.env.FRENTES_E2E_DADOS,
      FRENTES_PORT: String(PORTA),
      FRENTES_ABRIR_NAVEGADOR: 'false',
      FRENTES_HOJE_SIMULADO: HOJE,
    },
  },
})
