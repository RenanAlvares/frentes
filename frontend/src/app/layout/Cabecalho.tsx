import { Link } from 'react-router'
import { AbasPrincipais } from '@/app/layout/AbasPrincipais'
import { MenuGeral } from '@/app/layout/MenuGeral'
import { SinoAvisos } from '@/app/layout/SinoAvisos'
import { useSaude } from '@/app/layout/useSaude'
import { formatarData } from '@/lib/datas'

type Props = { totalAvisos: number; onAbrirAvisos: () => void }

// 01-produto §3. Busca e contador de "hoje" entram nas fases 3.5 e 6.
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
      <div className="mx-auto flex h-14 max-w-screen-2xl items-center gap-6 px-4">
        <div className="flex items-baseline gap-2">
          <Link to="/" className="text-lg font-semibold">
            Frentes
          </Link>
          {saude && <span className="text-xs text-muted-foreground">v{saude.versao}</span>}
        </div>
        <AbasPrincipais />
        <div className="ml-auto flex items-center gap-1">
          <SinoAvisos total={totalAvisos} onAbrir={onAbrirAvisos} />
          <MenuGeral />
        </div>
      </div>
    </header>
  )
}
