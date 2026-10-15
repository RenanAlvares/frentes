import { Check } from 'lucide-react'
import { CORES_PROJETO, LISTA_CORES_PROJETO, type CorProjeto } from '@/lib/cores'
import { cn } from '@/lib/utils'

type Props = {
  id?: string
  valor: CorProjeto
  onChange: (cor: CorProjeto) => void
}

/** As 8 cores de projeto (RN-11) como grupo de opções. */
export function SeletorCor({ id, valor, onChange }: Props) {
  return (
    <div id={id} role="radiogroup" aria-label="Cor" className="flex flex-wrap gap-2">
      {LISTA_CORES_PROJETO.map((cor) => {
        const selecionada = cor === valor
        return (
          <button
            key={cor}
            type="button"
            role="radio"
            aria-checked={selecionada}
            aria-label={CORES_PROJETO[cor].rotulo}
            title={CORES_PROJETO[cor].rotulo}
            onClick={() => onChange(cor)}
            className={cn(
              'flex size-7 items-center justify-center rounded-full text-white outline-none',
              'focus-visible:ring-3 focus-visible:ring-ring/50',
              selecionada && 'ring-2 ring-foreground ring-offset-2',
              CORES_PROJETO[cor].fundo,
            )}
          >
            {selecionada && <Check className="size-4" />}
          </button>
        )
      })}
    </div>
  )
}
