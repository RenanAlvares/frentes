import { Link } from 'react-router'
import { AbasPrincipais } from '@/app/layout/AbasPrincipais'
import { MenuGeral } from '@/app/layout/MenuGeral'
import { useSaude } from '@/app/layout/useSaude'

// 01-produto §3. Sino de avisos, busca e contador de "hoje" entram nas fases 3 e 6.
export function Cabecalho() {
  const { data: saude } = useSaude()

  return (
    <header className="sticky top-0 z-40 border-b bg-white">
      <div className="mx-auto flex h-14 max-w-screen-2xl items-center gap-6 px-4">
        <div className="flex items-baseline gap-2">
          <Link to="/" className="text-lg font-semibold">
            Frentes
          </Link>
          {saude && <span className="text-xs text-muted-foreground">v{saude.versao}</span>}
        </div>
        <AbasPrincipais />
        <div className="ml-auto">
          <MenuGeral />
        </div>
      </div>
    </header>
  )
}
