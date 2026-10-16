import type { components } from '@/api/schema'

/** RN-13: total 0 → barra vazia e "Sem tarefas". */
export function BarraProgresso({ concluidas, total }: components['schemas']['Progresso']) {
  const percentual = total > 0 ? Math.round((concluidas / total) * 100) : 0
  return (
    <div className="flex flex-col gap-1">
      <div
        role="progressbar"
        aria-label="Progresso"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percentual}
        className="h-1.5 overflow-hidden rounded-full bg-muted"
      >
        <div className="h-full bg-foreground/70" style={{ width: `${percentual}%` }} />
      </div>
      <p className="text-xs text-muted-foreground">
        {total > 0 ? `${concluidas}/${total} tarefas` : 'Sem tarefas'}
      </p>
    </div>
  )
}
