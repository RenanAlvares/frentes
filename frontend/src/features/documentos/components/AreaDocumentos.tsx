import { Folder, Plus, Upload, X } from 'lucide-react'
import { type DragEvent, useRef, useState } from 'react'
import { mensagemDoErro } from '@/api/erros'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ItemDocumento } from '@/features/documentos/components/ItemDocumento'
import { type Envio, useDocumentos, useEnvios } from '@/features/documentos/hooks/useDocumentos'
import { AreaProjeto } from '@/features/projetos/components/AreaProjeto'
import { cn } from '@/lib/utils'

type Props = { projetoId: string }

/** Área de Documentos do projeto (01 §4.4): soltar ou escolher arquivos, envios e lista (RN-73). */
export function AreaDocumentos({ projetoId }: Props) {
  const { data: documentos, isPending, isError, error } = useDocumentos(projetoId)
  const { envios, enviar, dispensar } = useEnvios(projetoId)
  const seletor = useRef<HTMLInputElement>(null)
  const escolher = () => seletor.current?.click()

  let lista
  if (isPending) {
    lista = <Skeleton className="h-16 rounded-lg" />
  } else if (isError) {
    lista = (
      <p role="alert" className="text-sm text-destructive">
        {mensagemDoErro(error)}
      </p>
    )
  } else if (documentos.length === 0) {
    lista = <p className="px-1 text-sm text-muted-foreground">Nenhum documento.</p>
  } else {
    lista = (
      <ul className="grid gap-2">
        {documentos.map((documento) => (
          <ItemDocumento key={documento.id} documento={documento} />
        ))}
      </ul>
    )
  }

  return (
    <AreaProjeto
      area="documentos"
      titulo="Documentos"
      icone={Folder}
      acao={
        <Button variant="ghost" size="sm" onClick={escolher}>
          <Plus /> Documento
        </Button>
      }
    >
      <div className="grid gap-3">
        <ZonaEnvio onEscolher={escolher} onSoltar={enviar} />
        <input
          ref={seletor}
          type="file"
          multiple
          hidden
          aria-label="Arquivos para enviar"
          onChange={(evento) => {
            if (evento.target.files) enviar(Array.from(evento.target.files))
            // Limpa para o mesmo arquivo poder ser escolhido de novo.
            evento.target.value = ''
          }}
        />
        {envios.length > 0 && (
          <ul aria-label="Envios" className="grid gap-2">
            {envios.map((envio) => (
              <LinhaEnvio key={envio.id} envio={envio} onDispensar={() => dispensar(envio.id)} />
            ))}
          </ul>
        )}
        {lista}
      </div>
    </AreaProjeto>
  )
}

function ZonaEnvio({
  onEscolher,
  onSoltar,
}: {
  onEscolher: () => void
  onSoltar: (arquivos: File[]) => void
}) {
  const [sobre, setSobre] = useState(false)

  function soltar(evento: DragEvent) {
    evento.preventDefault()
    setSobre(false)
    onSoltar(Array.from(evento.dataTransfer.files))
  }

  return (
    <button
      type="button"
      onClick={onEscolher}
      onDragOver={(evento) => {
        evento.preventDefault()
        setSobre(true)
      }}
      onDragLeave={(evento) => {
        // Passar por cima do ícone (filho) também dispara `dragleave`: só sai de verdade fora da zona.
        if (!evento.currentTarget.contains(evento.relatedTarget as Node | null)) setSobre(false)
      }}
      onDrop={soltar}
      className={cn(
        'flex flex-col items-center gap-1 rounded-lg border-2 border-dashed px-3 py-4 text-center text-sm text-muted-foreground transition-colors hover:border-area-documentos',
        sobre && 'border-area-documentos bg-area-documentos-suave text-area-documentos',
      )}
    >
      <Upload className="size-5" aria-hidden />
      Solte arquivos aqui ou clique para enviar
    </button>
  )
}

function LinhaEnvio({ envio, onDispensar }: { envio: Envio; onDispensar: () => void }) {
  const porcentagem = Math.round(envio.progresso * 100)
  return (
    <li className="grid gap-1 rounded-lg border bg-white p-2 text-sm">
      <div className="flex items-center gap-2">
        <span className="min-w-0 flex-1 truncate">{envio.nome}</span>
        {envio.erro ? (
          <Button
            variant="ghost"
            size="icon-xs"
            aria-label={`Dispensar ${envio.nome}`}
            onClick={onDispensar}
          >
            <X />
          </Button>
        ) : (
          <span className="text-xs text-muted-foreground">{porcentagem}%</span>
        )}
      </div>
      {envio.erro ? (
        <p role="alert" className="text-xs text-destructive">
          {envio.erro}
        </p>
      ) : (
        <div
          role="progressbar"
          aria-label={`Enviando ${envio.nome}`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={porcentagem}
          className="h-1.5 overflow-hidden rounded-full bg-muted"
        >
          <div
            className="h-full bg-area-documentos transition-[width]"
            style={{ width: `${porcentagem}%` }}
          />
        </div>
      )}
    </li>
  )
}
