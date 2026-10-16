import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { CORES_AREA, type AreaProjeto as Area } from '@/lib/cores'
import { cn } from '@/lib/utils'

type Props = {
  area: Area
  titulo: string
  icone: LucideIcon
  /** Botão de adicionar do cabeçalho da área. */
  acao?: ReactNode
  className?: string
  children: ReactNode
}

/** 01 §4.4: cada área tem cabeçalho com fundo na cor dela, ícone, nome e botão de adicionar. */
export function AreaProjeto({ area, titulo, icone: Icone, acao, className, children }: Props) {
  return (
    <section
      aria-labelledby={`area-${area}`}
      className={cn('flex min-w-0 flex-col overflow-hidden rounded-xl border bg-white', className)}
    >
      <div
        className={cn(
          'flex items-center gap-2 px-4 py-2.5',
          CORES_AREA[area].fundo,
          CORES_AREA[area].texto,
        )}
      >
        <Icone className="size-4 shrink-0" aria-hidden />
        <h2 id={`area-${area}`} className="flex-1 font-semibold">
          {titulo}
        </h2>
        {acao}
      </div>
      <div className="flex-1 p-3">{children}</div>
    </section>
  )
}
