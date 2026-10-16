import type { components } from '@/api/schema'
import { formatarData } from '@/lib/datas'

type TarefaDetalhe = components['schemas']['TarefaDetalhe']

/**
 * 01 §4.5. Repetida: "Próxima: 21/10/2026 · toda segunda" e as últimas 5 conclusões.
 * Meta mensal: "2 de 4 neste mês" e as datas das execuções do mês. Simples: nada.
 */
export function ResumoTarefa({ tarefa }: { tarefa: TarefaDetalhe }) {
  const datas = tarefa.execucoes.map((execucao) => formatarData(execucao.data))

  if (tarefa.tipo === 'repetida' && tarefa.prazo) {
    return (
      <section
        aria-label="Repetição"
        className="grid gap-1 rounded-lg bg-muted/60 px-3 py-2 text-sm"
      >
        <p className="font-medium">
          Próxima: {formatarData(tarefa.prazo)} · {tarefa.recorrencia_descricao}
        </p>
        <p className="text-muted-foreground">
          {datas.length > 0
            ? `Últimas conclusões: ${datas.join(', ')}`
            : 'Ainda não foi concluída.'}
        </p>
      </section>
    )
  }

  if (tarefa.tipo === 'meta_mensal') {
    return (
      <section
        aria-label="Meta do mês"
        className="grid gap-1 rounded-lg bg-muted/60 px-3 py-2 text-sm"
      >
        <p className="font-medium">
          {tarefa.progresso_mes ?? 0} de {tarefa.meta_mensal} neste mês
        </p>
        <p className="text-muted-foreground">
          {datas.length > 0 ? `Feitas em: ${datas.join(', ')}` : 'Nenhuma execução neste mês.'}
        </p>
      </section>
    )
  }

  return null
}
