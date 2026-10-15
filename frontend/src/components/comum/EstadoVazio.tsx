import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

type Props = {
  icone: LucideIcon
  titulo: string
  children?: ReactNode
}

/** Tela ou área sem itens: ícone, frase e a ação principal. */
export function EstadoVazio({ icone: Icone, titulo, children }: Props) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed bg-white px-6 py-16 text-center">
      <div className="flex size-14 items-center justify-center rounded-full bg-muted">
        <Icone className="size-7 text-muted-foreground" aria-hidden />
      </div>
      <p className="text-lg font-medium">{titulo}</p>
      {children}
    </div>
  )
}
