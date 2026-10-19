import { Plus, StickyNote } from 'lucide-react'
import { useState } from 'react'
import { mensagemDoErro } from '@/api/erros'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { CardAnotacao } from '@/features/anotacoes/components/CardAnotacao'
import { ModalAnotacao } from '@/features/anotacoes/components/ModalAnotacao'
import type { Anotacao } from '@/features/anotacoes/formulario'
import { useAnotacoes } from '@/features/anotacoes/hooks/useAnotacoes'
import { AreaProjeto } from '@/features/projetos/components/AreaProjeto'

type Props = { projetoId: string }

/** Área de Anotações do projeto (01 §4.4): cards na ordem de RN-81 (já vem da API). */
export function AreaAnotacoes({ projetoId }: Props) {
  const { data: anotacoes, isPending, isError, error } = useAnotacoes(projetoId)
  // `undefined` = fechado; `null` = criar; uma anotação = editar.
  const [modal, setModal] = useState<Anotacao | null | undefined>(undefined)

  let conteudo
  if (isPending) {
    conteudo = <Skeleton className="h-24 rounded-lg" />
  } else if (isError) {
    conteudo = (
      <p role="alert" className="text-sm text-destructive">
        {mensagemDoErro(error)}
      </p>
    )
  } else if (anotacoes.length === 0) {
    conteudo = <p className="px-1 text-sm text-muted-foreground">Nenhuma anotação.</p>
  } else {
    conteudo = (
      <ul className="grid gap-2">
        {anotacoes.map((anotacao) => (
          <CardAnotacao key={anotacao.id} anotacao={anotacao} onAbrir={() => setModal(anotacao)} />
        ))}
      </ul>
    )
  }

  return (
    <AreaProjeto
      area="anotacoes"
      titulo="Anotações"
      icone={StickyNote}
      acao={
        <Button variant="ghost" size="sm" onClick={() => setModal(null)}>
          <Plus /> Anotação
        </Button>
      }
    >
      {conteudo}
      <ModalAnotacao
        key={modal === undefined ? 'fechado' : (modal?.id ?? 'nova')}
        projetoId={projetoId}
        aberto={modal !== undefined}
        anotacao={modal ?? undefined}
        onFechar={() => setModal(undefined)}
      />
    </AreaProjeto>
  )
}
