import { describe, expect, it } from 'vitest'
import { camposDoErro, criarErroApi, ErroApi, MENSAGEM_GENERICA, mensagemDoErro } from '@/api/erros'

describe('criarErroApi', () => {
  it('lê código, mensagem e campos do formato de 04-api', () => {
    const corpo = {
      erro: {
        codigo: 'validacao',
        mensagem: 'Revise os campos destacados.',
        campos: { nome: 'Informe o nome do projeto.' },
      },
    }

    const erro = criarErroApi(422, corpo)

    expect(erro).toBeInstanceOf(ErroApi)
    expect(erro.status).toBe(422)
    expect(erro.codigo).toBe('validacao')
    expect(erro.message).toBe('Revise os campos destacados.')
    expect(erro.campos).toEqual({ nome: 'Informe o nome do projeto.' })
  })

  it('sem campos devolve objeto vazio', () => {
    const erro = criarErroApi(404, { erro: { codigo: 'nao_encontrado', mensagem: 'Não existe.' } })

    expect(erro.campos).toEqual({})
  })

  it.each([
    [502, 'Bad Gateway', 'erro_interno'],
    [500, undefined, 'erro_interno'],
    [405, { detail: 'Method Not Allowed' }, 'requisicao_invalida'],
    [
      422,
      { erro: { codigo: 'validacao', mensagem: 'x', campos: { nome: 1 } } },
      'requisicao_invalida',
    ],
  ])('corpo fora do padrão (%s) vira erro genérico', (status, corpo, codigo) => {
    const erro = criarErroApi(status, corpo)

    expect(erro.codigo).toBe(codigo)
    expect(erro.message).toBe(MENSAGEM_GENERICA)
  })
})

describe('mensagemDoErro e camposDoErro', () => {
  it('usam o que veio da API', () => {
    const erro = criarErroApi(422, {
      erro: { codigo: 'validacao', mensagem: 'Revise.', campos: { nome: 'Obrigatório.' } },
    })

    expect(mensagemDoErro(erro)).toBe('Revise.')
    expect(camposDoErro(erro)).toEqual({ nome: 'Obrigatório.' })
  })

  it('falha de rede usa a mensagem genérica de 01 §5', () => {
    const erro = new TypeError('Failed to fetch')

    expect(mensagemDoErro(erro)).toBe('Não foi possível concluir a ação. Tente de novo.')
    expect(camposDoErro(erro)).toEqual({})
  })
})
