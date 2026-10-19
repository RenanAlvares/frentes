import { Link } from 'react-router'
import { AbasPrincipais } from '@/app/layout/AbasPrincipais'
import { MenuGeral } from '@/app/layout/MenuGeral'
import { SinoAvisos } from '@/app/layout/SinoAvisos'
import { BuscaGlobal } from '@/features/busca/components/BuscaGlobal'
import { useSaude } from '@/app/layout/useSaude'
import { formatarData } from '@/lib/datas'
import { cn, FOCO_VISIVEL } from '@/lib/utils'

type Props = { totalAvisos: number; onAbrirAvisos: () => void }

// 01-produto §3. 05 §7: abaixo de `sm` as abas descem para uma segunda linha.
export function Cabecalho({ totalAvisos, onAbrirAvisos }: Props) {
  const { data: saude } = useSaude()

  return (
    <header className="sticky top-0 z-40 border-b bg-white">
      {saude?.hoje_simulado && (
        // 06 §6: FRENTES_HOJE_SIMULADO ligado (só para teste manual).
        <p role="status" className="bg-amber-100 py-1 text-center text-sm text-amber-900">
          Data simulada: {formatarData(saude.hoje)}
        </p>
      )}
      <div className="mx-auto flex max-w-screen-2xl flex-wrap items-center gap-x-3 px-4 sm:h-14 sm:flex-nowrap sm:gap-x-6">
        <div className="flex h-14 items-center gap-2">
          <Link to="/" className={cn('text-lg font-semibold', FOCO_VISIVEL)}>
            Frentes
          </Link>
          {saude && (
            <span className="hidden text-xs text-muted-foreground sm:inline">v{saude.versao}</span>
          )}
        </div>
        <AbasPrincipais />
        <div className="ml-auto flex items-center gap-1">
          <BuscaGlobal />
          <SinoAvisos total={totalAvisos} onAbrir={onAbrirAvisos} />
          <MenuGeral />
        </div>
      </div>
    </header>
  )
}
