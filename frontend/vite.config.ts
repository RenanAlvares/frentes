import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { configDefaults } from 'vitest/config'

// 05 §2: em dev, /api vai para o uvicorn; o build é servido pelo back-end.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  build: {
    outDir: '../backend/app/static',
    emptyOutDir: true,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Ponta a ponta é do Playwright (`npm run e2e`).
    exclude: [...configDefaults.exclude, 'e2e/**'],
    restoreMocks: true,
    // Testes de modal (Radix + user-event) passam de 5 s com a suíte inteira em paralelo.
    testTimeout: 10_000,
    css: false,
  },
})
