import { anoDe, formatarData, formatarDataCurta } from '@/lib/datas'
import { cn } from '@/lib/utils'

type Props = {
  prazo: string
  /** "Hoje" da API (RN-01); sem ele, mostra a data completa e sem destaque de hoje. */
  hoje: string | undefined
  /** Calculado pela API (ex.: `atrasada`, RN-27). */
  vencido: boolean
  className?: string
}

/**
 * 05 §5: vencido em vermelho, hoje em âmbar, os demais neutros.
 * "Amanhã" em âmbar depende de `dias_restantes` da API, que a tarefa ainda não tem.
 */
export function TextoPrazo({ prazo, hoje, vencido, className }: Props) {
  const texto = hoje ? formatarDataCurta(prazo, anoDe(hoje)) : formatarData(prazo)
  const cor = vencido ? 'text-red-600' : prazo === hoje ? 'text-amber-600' : 'text-muted-foreground'
  return <span className={cn('text-xs', cor, className)}>{texto}</span>
}
