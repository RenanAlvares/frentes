import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  documento,
  falha,
  renderizarRota,
  simularEscrita,
  simularGet,
  sucesso,
} from '@/test/renderizar'

const ID = '11111111-1111-4111-8111-111111111111'

function comDocumentos(documentos: ReturnType<typeof documento>[] = []) {
  const get = simularGet({ '/api/projetos/{projeto_id}/documentos': documentos })
  renderizarRota(`/projetos/${ID}`)
  return { usuario: userEvent.setup(), get }
}

/** XMLHttpRequest falso: o teste controla o progresso e a resposta de cada envio. */
class XhrFalso {
  static envios: XhrFalso[] = []
  metodo = ''
  url = ''
  corpo: FormData | null = null
  status = 0
  response: unknown = null
  responseType = ''
  upload: { onprogress: ((evento: Partial<ProgressEvent>) => void) | null } = { onprogress: null }
  onload: (() => void) | null = null
  onerror: (() => void) | null = null

  open(metodo: string, url: string) {
    this.metodo = metodo
    this.url = url
  }

  send(corpo: FormData) {
    this.corpo = corpo
    XhrFalso.envios.push(this)
  }

  get arquivo() {
    return this.corpo?.get('arquivos') as File
  }

  progresso(enviados: number, total: number) {
    act(() => this.upload.onprogress?.({ lengthComputable: true, loaded: enviados, total }))
  }

  responder(status: number, corpo: unknown) {
    this.status = status
    this.response = corpo
    act(() => this.onload?.())
  }
}

beforeEach(() => {
  XhrFalso.envios = []
  vi.stubGlobal('XMLHttpRequest', XhrFalso)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

const arquivo = (nome: string, conteudo = 'conteudo') => new File([conteudo], nome)

describe('Lista de documentos (01 §4.4, RN-71)', () => {
  it('ícone, nome, tamanho e data; tipos seguros abrem em aba nova, os outros baixam', async () => {
    comDocumentos([
      documento({ id: 'd1', nome: 'Contrato.pdf' }),
      documento({
        id: 'd2',
        nome: 'Orçamento.xlsx',
        extensao: '.xlsx',
        mime: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        tamanho_bytes: 12_800,
        abre_no_navegador: false,
      }),
    ])

    const pdf = await screen.findByRole('link', { name: 'Contrato.pdf' })
    expect(pdf).toHaveAttribute('href', '/api/documentos/d1/arquivo')
    expect(pdf).toHaveAttribute('target', '_blank')
    expect(pdf).toHaveAttribute('rel', 'noopener noreferrer')
    expect(pdf).not.toHaveAttribute('download')
    expect(within(pdf.closest('li')!).getByText('1,2 MB · 14/10/2026')).toBeInTheDocument()

    const planilha = screen.getByRole('link', { name: 'Orçamento.xlsx' })
    expect(planilha).toHaveAttribute('download')
    expect(planilha).not.toHaveAttribute('target')
    expect(within(planilha.closest('li')!).getByText('12,5 KB · 14/10/2026')).toBeInTheDocument()
  })

  it('sem documentos: "Nenhum documento."', async () => {
    comDocumentos()

    expect(await screen.findByText('Nenhum documento.')).toBeInTheDocument()
  })

  it('menu Baixar força o download mesmo de PDF', async () => {
    const { usuario } = comDocumentos([documento({ id: 'd1', nome: 'Contrato.pdf' })])

    await usuario.click(await screen.findByRole('button', { name: 'Ações de Contrato.pdf' }))

    const baixar = await screen.findByRole('menuitem', { name: 'Baixar' })
    expect(baixar).toHaveAttribute('href', '/api/documentos/d1/arquivo')
    expect(baixar).toHaveAttribute('download')
  })
})

describe('Envio (01 §4.4: progresso por arquivo)', () => {
  it('um envio por arquivo, com barra de progresso; ao terminar, a lista é recarregada', async () => {
    const { usuario, get } = comDocumentos()
    await screen.findByText('Nenhum documento.')

    await usuario.upload(screen.getByLabelText('Arquivos para enviar'), [
      arquivo('a.pdf'),
      arquivo('b.png'),
    ])

    const [a, b] = XhrFalso.envios
    expect(XhrFalso.envios).toHaveLength(2)
    expect(a!.metodo).toBe('POST')
    expect(a!.url).toBe(`/api/projetos/${ID}/documentos`)
    expect(a!.arquivo.name).toBe('a.pdf')
    expect(b!.arquivo.name).toBe('b.png')

    a!.progresso(30, 100)
    expect(screen.getByRole('progressbar', { name: 'Enviando a.pdf' })).toHaveAttribute(
      'aria-valuenow',
      '30',
    )
    expect(screen.getByRole('progressbar', { name: 'Enviando b.png' })).toHaveAttribute(
      'aria-valuenow',
      '0',
    )

    const listas = () =>
      get.mock.calls.filter((chamada) => chamada[0] === '/api/projetos/{projeto_id}/documentos')
    const antes = listas().length
    a!.responder(201, [documento({ nome: 'a.pdf' })])

    await waitFor(() =>
      expect(screen.queryByRole('progressbar', { name: 'Enviando a.pdf' })).not.toBeInTheDocument(),
    )
    expect(listas().length).toBeGreaterThan(antes)
    expect(screen.getByRole('progressbar', { name: 'Enviando b.png' })).toBeInTheDocument()
  })

  it('arquivo acima do limite: a linha mostra a mensagem da API e pode ser dispensada', async () => {
    const { usuario } = comDocumentos()
    await screen.findByText('Nenhum documento.')

    await usuario.upload(screen.getByLabelText('Arquivos para enviar'), [arquivo('grande.bin')])
    XhrFalso.envios[0]!.responder(413, {
      erro: { codigo: 'arquivo_grande', mensagem: '“grande.bin” passa do limite de 50 MB.' },
    })

    expect(await screen.findByText('“grande.bin” passa do limite de 50 MB.')).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: 'Dispensar grande.bin' }))
    expect(screen.queryByText('grande.bin')).not.toBeInTheDocument()
  })

  it('soltar arquivos na área também envia', async () => {
    comDocumentos()
    const zona = await screen.findByRole('button', {
      name: 'Solte arquivos aqui ou clique para enviar',
    })

    fireEvent.dragOver(zona, { dataTransfer: { files: [] } })
    expect(zona).toHaveClass('bg-area-documentos-suave')
    fireEvent.drop(zona, { dataTransfer: { files: [arquivo('solto.txt')] } })

    expect(XhrFalso.envios.map((envio) => envio.arquivo.name)).toEqual(['solto.txt'])
    expect(zona).not.toHaveClass('bg-area-documentos-suave')
  })
})

describe('Renomear e excluir (RN-72, RN-90)', () => {
  it('Renomear abre o diálogo com o nome atual e envia o PATCH', async () => {
    const { usuario } = comDocumentos([documento({ id: 'd1', nome: 'Contrato.pdf' })])
    const patch = simularEscrita('PATCH', sucesso(documento({ nome: 'Novo.pdf' })))

    await usuario.click(await screen.findByRole('button', { name: 'Ações de Contrato.pdf' }))
    await usuario.click(await screen.findByRole('menuitem', { name: 'Renomear' }))
    const dialogo = within(await screen.findByRole('dialog', { name: 'Renomear documento' }))
    expect(dialogo.getByText('A extensão .pdf é mantida.')).toBeInTheDocument()
    const campo = dialogo.getByLabelText('Nome')
    expect(campo).toHaveValue('Contrato.pdf')
    await usuario.clear(campo)
    await usuario.type(campo, 'Novo')
    await usuario.click(dialogo.getByRole('button', { name: 'Salvar' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(patch).toHaveBeenCalledWith('/api/documentos/{documento_id}', {
      params: { path: { documento_id: 'd1' } },
      body: { nome: 'Novo' },
    })
  })

  it('nome com barra é recusado no formulário; 422 da API aparece no campo', async () => {
    const { usuario } = comDocumentos([documento({ id: 'd1', nome: 'Contrato.pdf' })])
    const patch = simularEscrita(
      'PATCH',
      falha(422, {
        erro: {
          codigo: 'validacao',
          mensagem: 'Revise os campos destacados.',
          campos: { nome: 'Use no máximo 255 caracteres, contando a extensão.' },
        },
      }),
    )

    await usuario.click(await screen.findByRole('button', { name: 'Ações de Contrato.pdf' }))
    await usuario.click(await screen.findByRole('menuitem', { name: 'Renomear' }))
    const dialogo = within(await screen.findByRole('dialog'))
    const campo = dialogo.getByLabelText('Nome')
    await usuario.clear(campo)
    await usuario.type(campo, 'a/b')
    await usuario.click(dialogo.getByRole('button', { name: 'Salvar' }))

    expect(await dialogo.findByText('O nome não pode ter / nem \\.')).toBeInTheDocument()
    expect(patch).not.toHaveBeenCalled()

    await usuario.clear(campo)
    await usuario.type(campo, 'longo')
    await usuario.click(dialogo.getByRole('button', { name: 'Salvar' }))

    expect(
      await dialogo.findByText('Use no máximo 255 caracteres, contando a extensão.'),
    ).toBeInTheDocument()
  })

  it('Excluir mostra "Movido para a lixeira" e Desfazer restaura', async () => {
    const { usuario } = comDocumentos([documento({ id: 'd1', nome: 'Contrato.pdf' })])
    const excluir = simularEscrita('DELETE', sucesso(undefined, 204))
    const restaurar = simularEscrita('POST', sucesso(undefined, 204))

    await usuario.click(await screen.findByRole('button', { name: 'Ações de Contrato.pdf' }))
    await usuario.click(await screen.findByRole('menuitem', { name: 'Excluir' }))

    expect(await screen.findByText('Movido para a lixeira')).toBeInTheDocument()
    expect(excluir).toHaveBeenCalledWith('/api/documentos/{documento_id}', {
      params: { path: { documento_id: 'd1' } },
    })
    await usuario.click(screen.getByRole('button', { name: 'Desfazer' }))
    await waitFor(() =>
      expect(restaurar).toHaveBeenCalledWith('/api/lixeira/{tipo}/{item_id}/restaurar', {
        params: { path: { tipo: 'documento', item_id: 'd1' } },
      }),
    )
  })
})
