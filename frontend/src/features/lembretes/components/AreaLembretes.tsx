import { Bell, Plus } from 'lucide-react'
import { useState } from 'react'
import { mensagemDoErro } from '@/api/erros'
import { useSaude } from '@/app/layout/useSaude'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { AreaProjeto } from '@/features/projetos/components/AreaProjeto'
import { ItemLembrete } from '@/features/lembretes/components/ItemLembrete'
import { ModalLembrete } from '@/features/lembretes/components/ModalLembrete'
import { SecaoConcluidos } from '@/features/lembretes/components/SecaoConcluidos'
import type { Lembrete } from '@/features/lembretes/formulario'
import { useLembretes } from '@/features/lembretes/hooks/useLembretes'

type Props = { projetoId: string; className?: string }

/** Área de Lembretes do projeto (01 §4.4): ativos por vencimento (RN-45) e Concluídos. */
export function AreaLembretes({ projetoId, className }: Props) {
  const { data, isPending, isError, error } = useLembretes(projetoId)
  const { data: saude } = useSaude()
  // `undefined` = fechado; `null` = criar; um lembrete = editar.
  const [modal, setModal] = useState<Lembrete | null | undefined>(undefined)

  let conteudo
  if (isPending) {
    conteudo = <Skeleton className="h-24 rounded-lg" />
  } else if (isError) {
    conteudo = (
      <p role="alert" className="text-sm text-destructive">
        {mensagemDoErro(error)}
      </p>
    )
  } else {
    conteudo = (
      <div className="grid gap-3">
        {data.ativos.length === 0 ? (
          <p className="px-1 text-sm text-muted-foreground">Nenhum lembrete.</p>
        ) : (
          <ul className="grid gap-2">
            {data.ativos.map((lembrete) => (
              <ItemLembrete
                key={lembrete.id}
                lembrete={lembrete}
                hoje={saude?.hoje}
                onEditar={() => setModal(lembrete)}
              />
            ))}
          </ul>
        )}
        <SecaoConcluidos projetoId={projetoId} lembretes={data.concluidos} />
      </div>
    )
  }

  return (
    <AreaProjeto
      area="lembretes"
      titulo="Lembretes"
      icone={Bell}
      className={className}
      acao={
        <Button variant="ghost" size="sm" onClick={() => setModal(null)}>
          <Plus /> Lembrete
        </Button>
      }
    >
      {conteudo}
      <ModalLembrete
        key={modal === undefined ? 'fechado' : (modal?.id ?? 'novo')}
        projetoId={projetoId}
        aberto={modal !== undefined}
        lembrete={modal ?? undefined}
        onFechar={() => setModal(undefined)}
      />
    </AreaProjeto>
  )
}
