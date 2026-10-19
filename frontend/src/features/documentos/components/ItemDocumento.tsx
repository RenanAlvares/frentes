import { Download, Ellipsis, Pencil, Trash2 } from 'lucide-react'
import { createElement, useState } from 'react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { DialogoRenomear } from '@/features/documentos/components/DialogoRenomear'
import { formatarTamanho, iconeDoDocumento } from '@/features/documentos/formato'
import {
  useExcluirDocumento,
  useRestaurarDocumento,
} from '@/features/documentos/hooks/useDocumentos'
import { type Documento, urlDoArquivo } from '@/features/documentos/upload'
import { formatarCarimbo } from '@/lib/datas'
import { avisarComDesfazer } from '@/lib/desfazer'

type Props = { documento: Documento }

/** 01 §4.4: ícone pelo tipo, nome, tamanho e data; clique abre ou baixa (RN-71). */
export function ItemDocumento({ documento }: Props) {
  const excluir = useExcluirDocumento(documento.projeto_id)
  const restaurar = useRestaurarDocumento(documento.projeto_id)
  const [renomeando, setRenomeando] = useState(false)
  const url = urlDoArquivo(documento.id)
  // Tipos seguros abrem numa aba nova; os outros a API já manda como download.
  const abrir = documento.abre_no_navegador
    ? { target: '_blank', rel: 'noopener noreferrer' }
    : { download: '' }

  function excluirDocumento() {
    excluir.mutate(documento.id, {
      onError: (erro) => toast.error(mensagemDoErro(erro)),
      onSuccess: () =>
        avisarComDesfazer('Movido para a lixeira', () => restaurar.mutateAsync(documento.id)),
    })
  }

  return (
    <li className="flex items-center gap-2 rounded-lg border bg-white p-2 text-sm">
      {createElement(iconeDoDocumento(documento.extensao, documento.mime), {
        className: 'size-5 shrink-0 text-area-documentos',
        'aria-hidden': true,
      })}
      <div className="min-w-0 flex-1">
        <a
          href={url}
          {...abrir}
          title={documento.nome}
          className="block truncate font-medium hover:underline"
        >
          {documento.nome}
        </a>
        <p className="text-xs text-muted-foreground">
          {formatarTamanho(documento.tamanho_bytes)} · {formatarCarimbo(documento.criado_em)}
        </p>
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon-xs" aria-label={`Ações de ${documento.nome}`}>
            <Ellipsis />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={() => setRenomeando(true)}>
            <Pencil /> Renomear
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            {/* `download` força baixar até os tipos que abririam no navegador. */}
            <a href={url} download="">
              <Download /> Baixar
            </a>
          </DropdownMenuItem>
          <DropdownMenuItem variant="destructive" onSelect={excluirDocumento}>
            <Trash2 /> Excluir
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      {renomeando && (
        <DialogoRenomear documento={documento} aberto onFechar={() => setRenomeando(false)} />
      )}
    </li>
  )
}
