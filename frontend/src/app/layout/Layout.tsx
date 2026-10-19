import { Outlet } from 'react-router'
import { Cabecalho } from '@/app/layout/Cabecalho'
import { PainelAvisos } from '@/features/avisos/components/PainelAvisos'
import { usePainelAvisos } from '@/features/avisos/hooks/useAvisos'

export function Layout() {
  // 05 §8: os avisos são buscados ao montar o layout; painel e sino dividem o estado.
  const avisos = usePainelAvisos()

  return (
    <div className="min-h-svh bg-neutral-50">
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
