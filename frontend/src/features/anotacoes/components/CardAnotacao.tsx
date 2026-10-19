import { Pin } from 'lucide-react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { Button } from '@/components/ui/button'
import type { Anotacao } from '@/features/anotacoes/formulario'
import { useAtualizarAnotacao } from '@/features/anotacoes/hooks/useAnotacoes'
import { CORES_ANOTACAO } from '@/lib/cores'
import { cn, FOCO_VISIVEL } from '@/lib/utils'

type Props = { anotacao: Anotacao; onAbrir: () => void }

/** 01 §4.4: card colorido com título (opcional) e até 4 linhas do texto; alfinete nas fixadas. */
export function CardAnotacao({ anotacao, onAbrir }: Props) {
  const atualizar = useAtualizarAnotacao(anotacao.projeto_id)
  const rotulo = anotacao.titulo || anotacao.texto

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
        'relative rounded-lg p-3 text-sm shadow-xs',
        CORES_ANOTACAO[anotacao.cor].fundo,
      )}
    >
      <button
        type="button"
        onClick={onAbrir}
        aria-label={`Abrir anotação ${rotulo}`}
        className={cn('grid w-full gap-1 pr-6 text-left', FOCO_VISIVEL)}
      >
        {anotacao.titulo && <span className="font-semibold break-words">{anotacao.titulo}</span>}
        <span className="line-clamp-4 whitespace-pre-wrap break-words">{anotacao.texto}</span>
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
