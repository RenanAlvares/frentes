import { Pin } from 'lucide-react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { Button } from '@/components/ui/button'
import type { Anotacao } from '@/features/anotacoes/formulario'
import { useAtualizarAnotacao } from '@/features/anotacoes/hooks/useAnotacoes'
import { CORES_ANOTACAO } from '@/lib/cores'
import { cn, FOCO_VISIVEL } from '@/lib/utils'

type Props = { anotacao: Anotacao; onAbrir: () => void }

/** 01 §4.4: o título (ou a primeira linha do texto) e uma linha de prévia do resto. */
function resumir({ titulo, texto }: Anotacao) {
  const linhas = texto
    .split('\n')
    .map((linha) => linha.trim())
    .filter(Boolean)
  if (titulo) return { titulo, previa: linhas.join(' ') }
  return { titulo: linhas[0] ?? '', previa: linhas.slice(1).join(' ') }
}

/**
 * 01 §4.4: card colorido e compacto (título + uma linha de prévia; o texto completo fica no
 * modal); alfinete nas fixadas.
 */
export function CardAnotacao({ anotacao, onAbrir }: Props) {
  const atualizar = useAtualizarAnotacao(anotacao.projeto_id)
  const { titulo: rotulo, previa } = resumir(anotacao)

  // RN-85: fixar é ação direta (salva na hora, sem o modal).
  function alternarFixada() {
    atualizar.mutate(
      { id: anotacao.id, dados: { fixada: !anotacao.fixada } },
      { onError: (erro) => toast.error(mensagemDoErro(erro)) },
    )
  }

  return (
    <li
      className={cn(
        'relative rounded-lg p-3 text-sm shadow-sm transition-shadow hover:shadow-md',
        CORES_ANOTACAO[anotacao.cor].fundo,
      )}
    >
      <button
        type="button"
        onClick={onAbrir}
        aria-label={`Abrir anotação ${rotulo}`}
        className={cn('grid w-full min-w-0 gap-0.5 pr-6 text-left', FOCO_VISIVEL)}
      >
        <span className="truncate font-semibold">{rotulo}</span>
        {previa && <span className="truncate text-xs text-foreground/70">{previa}</span>}
      </button>
      <Button
        variant="ghost"
        size="icon-xs"
        className="absolute top-1.5 right-1.5"
        aria-label={anotacao.fixada ? `Desafixar ${rotulo}` : `Fixar ${rotulo}`}
        aria-pressed={anotacao.fixada}
        disabled={atualizar.isPending}
        onClick={alternarFixada}
      >
        <Pin className={cn(anotacao.fixada ? 'fill-current' : 'opacity-40')} />
      </Button>
    </li>
  )
}
