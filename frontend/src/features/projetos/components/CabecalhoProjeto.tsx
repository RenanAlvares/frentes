import { ArrowLeft, ChevronDown, Ellipsis, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import type { components } from '@/api/schema'
import { useSaude } from '@/app/layout/useSaude'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { BarraProgresso } from '@/features/projetos/components/BarraProgresso'
import { ModalProjeto } from '@/features/projetos/components/ModalProjeto'
import { useAtualizarProjeto, useExcluirComDesfazer } from '@/features/projetos/hooks/useProjetos'
import { LISTA_STATUS, ROTULO_STATUS, type StatusProjeto } from '@/features/projetos/status'
import { CORES_PROJETO } from '@/lib/cores'
import { anoDe, formatarData, formatarDataCurta } from '@/lib/datas'
import { cn, FOCO_VISIVEL } from '@/lib/utils'

type Props = { projeto: components['schemas']['Projeto'] }

/** 01 §4.4: voltar, nome, status (trocável), datas, menu; progresso e descrição. */
export function CabecalhoProjeto({ projeto }: Props) {
  const navegar = useNavigate()
  const local = useLocation()
  const { data: saude } = useSaude()
  const atualizar = useAtualizarProjeto()
  const excluir = useExcluirComDesfazer()
  const [editando, setEditando] = useState(false)
  const [descricaoAberta, setDescricaoAberta] = useState(false)

  // Volta para a tela de onde veio; aberto por link direto, vai para a home.
  const voltar = () => (local.key === 'default' ? navegar('/') : navegar(-1))
  const data = (iso: string) =>
    saude ? formatarDataCurta(iso, anoDe(saude.hoje)) : formatarData(iso)
  const datas = [
    projeto.data_inicio && `Início ${data(projeto.data_inicio)}`,
    projeto.prazo && `Prazo ${data(projeto.prazo)}`,
  ].filter(Boolean)

  function trocarStatus(status: string) {
    atualizar.mutate(
      { id: projeto.id, dados: { status: status as StatusProjeto } },
      { onError: (erro) => toast.error(mensagemDoErro(erro)) },
    )
  }

  return (
    <div className="flex flex-col gap-3 overflow-hidden rounded-xl border bg-white">
      <div className={cn('h-1.5', CORES_PROJETO[projeto.cor].fundo)} />
      <div className="flex flex-col gap-3 px-4 pb-4">
        {/* Voltar e o menu ficam nas pontas; só o meio (nome, status, datas) quebra linha (05 §7). */}
        <div className="flex items-start gap-x-3">
          <Button variant="ghost" size="icon" aria-label="Voltar" onClick={voltar}>
            <ArrowLeft />
          </Button>
          <div className="flex min-h-9 min-w-0 flex-1 flex-wrap items-center gap-x-3 gap-y-2">
            <h1 className="text-xl font-semibold break-words">{projeto.nome}</h1>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-6 rounded-full px-2.5 text-xs"
                  aria-label={`Status: ${ROTULO_STATUS[projeto.status]}. Trocar status`}
                >
                  {ROTULO_STATUS[projeto.status]} <ChevronDown />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuRadioGroup value={projeto.status} onValueChange={trocarStatus}>
                  {LISTA_STATUS.map((status) => (
                    <DropdownMenuRadioItem key={status} value={status}>
                      {ROTULO_STATUS[status]}
                    </DropdownMenuRadioItem>
                  ))}
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>
            {datas.length > 0 && (
              <p className="text-sm text-muted-foreground">{datas.join(' · ')}</p>
            )}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Ações do projeto">
                <Ellipsis />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onSelect={() => setEditando(true)}>
                <Pencil /> Editar projeto
              </DropdownMenuItem>
              <DropdownMenuItem
                variant="destructive"
                onSelect={() => excluir(projeto.id, () => navegar('/'))}
              >
                <Trash2 /> Excluir projeto
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        {projeto.progresso && <BarraProgresso {...projeto.progresso} />}
        {projeto.descricao && (
          <button
            type="button"
            aria-expanded={descricaoAberta}
            onClick={() => setDescricaoAberta(!descricaoAberta)}
            className={cn(
              'text-left text-sm whitespace-pre-line text-muted-foreground',
              FOCO_VISIVEL,
              !descricaoAberta && 'truncate whitespace-nowrap',
            )}
          >
            {projeto.descricao}
          </button>
        )}
      </div>
      <ModalProjeto aberto={editando} projetoId={projeto.id} onFechar={() => setEditando(false)} />
    </div>
  )
}
