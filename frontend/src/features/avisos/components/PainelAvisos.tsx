import { BellRing, X } from 'lucide-react'
import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ItemAviso } from '@/features/avisos/components/ItemAviso'
import { type Aviso, chaveDoAviso } from '@/features/avisos/hooks/useAvisos'

const PRIMEIROS = 3

type Props = {
  /** Já na ordem da API (RN-51) e sem os itens tratados no painel (RN-54). */
  itens: Aviso[]
  onFechar: () => void
  onTratado: (chave: string, tratado: boolean) => void
}

/** 01 §4.1 / RN-52..55: topo do conteúdo, não bloqueia a tela; sem avisos, não aparece. */
export function PainelAvisos({ itens, onFechar, onTratado }: Props) {
  const [expandido, setExpandido] = useState(false)
  if (itens.length === 0) return null

  const visiveis = expandido ? itens : itens.slice(0, PRIMEIROS)
  const restantes = itens.length - visiveis.length
  return (
    <section
      aria-labelledby="titulo-avisos"
      className="mb-6 grid gap-3 rounded-xl border border-l-4 border-amber-300 border-l-amber-500 bg-amber-50 p-4 shadow-sm"
    >
      <div className="flex items-start gap-3">
        <span
          aria-hidden
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-amber-500 text-white"
        >
          <BellRing className="size-5" />
        </span>
        <div className="grid gap-0.5">
          <div className="flex items-center gap-2">
            <h2 id="titulo-avisos" className="text-base font-semibold">
              Avisos
            </h2>
            <Badge className="bg-amber-500 text-white" aria-label={`${itens.length} no total`}>
              {itens.length}
            </Badge>
          </div>
          <p className="text-xs text-amber-900">Vencidos ou com prazo nos próximos dias</p>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          className="ml-auto"
          aria-label="Fechar avisos"
          onClick={onFechar}
        >
          <X />
        </Button>
      </div>
      <ul className="grid gap-2">
        {visiveis.map((aviso) => {
          const chave = chaveDoAviso(aviso)
          return (
            <ItemAviso
              key={chave}
              aviso={aviso}
              onTratado={(tratado) => onTratado(chave, tratado)}
            />
          )
        })}
      </ul>
      {restantes > 0 && (
        <Button
          variant="outline"
          size="sm"
          className="justify-self-start bg-white"
          onClick={() => setExpandido(true)}
        >
          Ver mais {restantes}
        </Button>
      )}
    </section>
  )
}
