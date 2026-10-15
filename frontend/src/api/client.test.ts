import { describe, expect, it } from 'vitest'
import { exigir } from '@/api/client'
import { ErroApi } from '@/api/erros'

describe('exigir', () => {
  it('devolve os dados de uma resposta de sucesso', async () => {
    const resultado = { data: { versao: '1.0.0' }, response: new Response(null, { status: 200 }) }

    await expect(exigir(Promise.resolve(resultado))).resolves.toEqual({ versao: '1.0.0' })
  })

  it('lança ErroApi com o status e o corpo do erro', async () => {
    const resultado = {
      error: { erro: { codigo: 'nao_encontrado', mensagem: 'Projeto não encontrado.' } },
      response: new Response(null, { status: 404 }),
    }

    const erro = await exigir(Promise.resolve(resultado)).catch((e: unknown) => e)

    expect(erro).toBeInstanceOf(ErroApi)
    expect(erro).toMatchObject({ status: 404, codigo: 'nao_encontrado' })
    expect((erro as ErroApi).message).toBe('Projeto não encontrado.')
  })
})
