import type { ReactNode } from 'react'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

type Props = {
  id: string
  rotulo: string
  /** Mensagem de erro abaixo do campo (01 §4.6), com id `${id}-erro`. */
  erro?: string
  /** Rótulo só para leitores de tela (ex.: chips do modal da tarefa). */
  rotuloOculto?: boolean
  className?: string
  children: ReactNode
}

export function CampoForm({ id, rotulo, erro, rotuloOculto, className, children }: Props) {
  return (
    <div className={cn('grid gap-1.5', className)}>
      <Label htmlFor={id} className={cn(rotuloOculto && 'sr-only')}>
        {rotulo}
      </Label>
      {children}
      {erro && (
        <p id={`${id}-erro`} className="text-sm text-destructive">
          {erro}
        </p>
      )}
    </div>
  )
}
