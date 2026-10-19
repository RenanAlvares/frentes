import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderizarRota, simularEscrita, simularGet, sucesso } from '@/test/renderizar'

const AVISO = 'Avisar tarefas com prazo com quantos dias de antecedência'
const ANTECEDENCIA = 'Antecedência padrão de novos lembretes'

function comConfiguracoes(aviso = 3, antecedencia = 5) {
  simularGet({
    '/api/configuracoes': {
      aviso_tarefas_dias: aviso,
      antecedencia_padrao_lembretes: antecedencia,
    },
  })
  renderizarRota('/configuracoes')
  return userEvent.setup()
}

describe('PaginaConfiguracoes (01 §4.9, RN-100)', () => {
  it('mostra os valores atuais e a versão do app; Salvar começa desabilitado', async () => {
    comConfiguracoes(3, 5)

    expect(await screen.findByLabelText(AVISO)).toHaveValue(3)
    expect(screen.getByLabelText(ANTECEDENCIA)).toHaveValue(5)
    expect(screen.getByText('Frentes versão 1.2.3')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Salvar' })).toBeDisabled()
  })

  it('Salvar envia só o que mudou e mostra "Configurações salvas"', async () => {
    const usuario = comConfiguracoes(3, 5)
    const patch = simularEscrita(
      'PATCH',
      sucesso({ aviso_tarefas_dias: 7, antecedencia_padrao_lembretes: 5 }),
    )

    const campo = await screen.findByLabelText(AVISO)
    await usuario.clear(campo)
    await usuario.type(campo, '7')
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))

    expect(await screen.findByText('Configurações salvas')).toBeInTheDocument()
    expect(patch).toHaveBeenCalledWith('/api/configuracoes', { body: { aviso_tarefas_dias: 7 } })
    await waitFor(() => expect(screen.getByRole('button', { name: 'Salvar' })).toBeDisabled())
  })

  it('fora de 0 a 60 ou vazio: erro abaixo do campo, sem chamar a API', async () => {
    const usuario = comConfiguracoes()
    const patch = simularEscrita('PATCH', sucesso({}))

    const campo = await screen.findByLabelText(ANTECEDENCIA)
    await usuario.clear(campo)
    await usuario.type(campo, '61')
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))
    expect(await screen.findByText('Use de 0 a 60 dias.')).toBeInTheDocument()

    await usuario.clear(campo)
    await usuario.click(screen.getByRole('button', { name: 'Salvar' }))
    expect(await screen.findByText('Informe um número de 0 a 60.')).toBeInTheDocument()
    expect(patch).not.toHaveBeenCalled()
  })
})
