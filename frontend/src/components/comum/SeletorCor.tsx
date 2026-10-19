import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

export type OpcaoDeCor = {
  rotulo: string
  /** Classes da amostra (fundo, e borda se houver). */
  fundo: string
  /** Cor do ✓ sobre a amostra; padrão branco. */
  texto?: string
}

type Props<C extends string> = {
  id?: string
  valor: C
  onChange: (cor: C) => void
  /** Ex.: `CORES_PROJETO` (RN-11) ou `CORES_ANOTACAO` (RN-80). */
  paleta: Record<C, OpcaoDeCor>
}

/** As cores da paleta como grupo de opções. */
export function SeletorCor<C extends string>({ id, valor, onChange, paleta }: Props<C>) {
  const cores = Object.keys(paleta) as C[]
  return (
    <div id={id} role="radiogroup" aria-label="Cor" className="flex flex-wrap gap-2">
      {cores.map((cor) => {
        const selecionada = cor === valor
        const { rotulo, fundo, texto = 'text-white' } = paleta[cor]
        return (
          <button
            key={cor}
            type="button"
            role="radio"
            aria-checked={selecionada}
            aria-label={rotulo}
            title={rotulo}
            onClick={() => onChange(cor)}
            className={cn(
              'flex size-7 items-center justify-center rounded-full outline-none',
              'focus-visible:ring-3 focus-visible:ring-ring/50',
              selecionada && 'ring-2 ring-foreground ring-offset-2',
              fundo,
              texto,
            )}
          >
            {selecionada && <Check className="size-4" />}
          </button>
        )
      })}
    </div>
  )
}
