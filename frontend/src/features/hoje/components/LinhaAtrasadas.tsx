import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { ItemHoje, type TarefaHoje } from '@/features/hoje/components/ItemHoje'
import { cn } from '@/lib/utils'

/** RN-61: o estado expandido vale durante a sessão do navegador. */
const CHAVE_SESSAO = 'frentes:hoje:atrasadas-expandidas'

function lerExpandida() {
  try {
    return sessionStorage.getItem(CHAVE_SESSAO) === '1'
  } catch {
    return false
  }
}

function gravarExpandida(expandida: boolean) {
  try {
    sessionStorage.setItem(CHAVE_SESSAO, expandida ? '1' : '0')
  } catch {
    // Sem storage (aba privada, bloqueio): só não lembra.
  }
}

type Props = { tarefas: TarefaHoje[]; onAbrir: (tarefaId: string) => void }

/** 01 §4.3 / RN-61: "N atrasadas ›" em vermelho, recolhida; some quando N = 0. */
export function LinhaAtrasadas({ tarefas, onAbrir }: Props) {
  const [expandida, setExpandida] = useState(lerExpandida)
  if (tarefas.length === 0) return null

  function alternar() {
    setExpandida(!expandida)
    gravarExpandida(!expandida)
  }

  const total = tarefas.length
  return (
    <section aria-label="Atrasadas" className="grid gap-2">
      <button
        type="button"
        aria-expanded={expandida}
        onClick={alternar}
        className="flex items-center gap-1 justify-self-start text-sm font-semibold text-red-600"
      >
        {total} {total === 1 ? 'atrasada' : 'atrasadas'}
        <ChevronRight
          aria-hidden
          className={cn('size-4 transition-transform', expandida && 'rotate-90')}
        />
      </button>
      {expandida && (
        <ul className="grid gap-2">
          {tarefas.map((tarefa) => (
            <ItemHoje key={tarefa.id} tarefa={tarefa} onAbrir={onAbrir} />
          ))}
        </ul>
      )}
    </section>
  )
}
