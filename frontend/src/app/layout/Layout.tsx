import { Outlet } from 'react-router'
import { Cabecalho } from '@/app/layout/Cabecalho'
import { PainelAvisos } from '@/features/avisos/components/PainelAvisos'
import { usePainelAvisos } from '@/features/avisos/hooks/useAvisos'
import { useAtalho } from '@/lib/atalhos'

export function Layout() {
  // 05 §8: os avisos são buscados ao montar o layout; painel e sino dividem o estado.
  const avisos = usePainelAvisos()
  // RN-130: `Esc` fecha o painel de avisos (modais fecham pelo Radix).
  const painelVisivel = !avisos.fechado && avisos.itens.length > 0
  useAtalho('Escape', avisos.fechar, painelVisivel)

  return (
    <div className="min-h-svh bg-neutral-100">
      <Cabecalho totalAvisos={avisos.itens.length} onAbrirAvisos={avisos.abrir} />
      <main className="mx-auto max-w-screen-2xl px-4 py-6">
        {!avisos.fechado && (
          <PainelAvisos itens={avisos.itens} onFechar={avisos.fechar} onTratado={avisos.marcar} />
        )}
        <Outlet />
      </main>
    </div>
  )
}
