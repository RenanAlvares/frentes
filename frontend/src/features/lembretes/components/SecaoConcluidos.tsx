import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { Button } from '@/components/ui/button'
import type { Lembrete } from '@/features/lembretes/formulario'
import { useDesfazerBaixa } from '@/features/lembretes/hooks/useLembretes'
import { formatarCarimbo } from '@/lib/datas'
import { cn } from '@/lib/utils'

/** 01 §4.4: seção recolhida "Concluídos (N)" com "Reativar" (RN-44, mesmo endpoint do desfazer). */
export function SecaoConcluidos({
  projetoId,
  lembretes,
}: {
  projetoId: string
  lembretes: Lembrete[]
}) {
  const [aberta, setAberta] = useState(false)
  const reativar = useDesfazerBaixa(projetoId)
  if (lembretes.length === 0) return null

  return (
    <div className="grid gap-2">
      <button
        type="button"
        aria-expanded={aberta}
        onClick={() => setAberta(!aberta)}
        className="flex items-center gap-1 text-left text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronRight className={cn('size-4 transition-transform', aberta && 'rotate-90')} />
        Concluídos ({lembretes.length})
      </button>
      {aberta && (
        <ul className="grid gap-1">
          {lembretes.map((lembrete) => (
            <li key={lembrete.id} className="flex items-center gap-2 rounded-lg px-2 py-1 text-sm">
              <div className="min-w-0 flex-1">
                <p className="truncate text-muted-foreground line-through">{lembrete.titulo}</p>
                {lembrete.concluido_em && (
                  <p className="text-xs text-muted-foreground">
                    Concluído em {formatarCarimbo(lembrete.concluido_em)}
                  </p>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                aria-label={`Reativar ${lembrete.titulo}`}
                disabled={reativar.isPending}
                onClick={() =>
                  reativar.mutate(lembrete.id, {
                    onError: (erro) => toast.error(mensagemDoErro(erro)),
                  })
                }
              >
                Reativar
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
