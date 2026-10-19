import { Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'

type Props = { total: number; onAbrir: () => void }

/** RN-55: mostra o total (oculto com 0) e reabre o painel de avisos. */
export function SinoAvisos({ total, onAbrir }: Props) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="relative"
      aria-label={total > 0 ? `Avisos: ${total}` : 'Avisos'}
      onClick={onAbrir}
    >
      <Bell />
      {total > 0 && (
        <span
          aria-hidden
          className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] leading-none font-semibold text-white"
        >
          {total}
        </span>
      )}
    </Button>
  )
}
