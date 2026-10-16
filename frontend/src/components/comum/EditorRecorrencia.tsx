import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { formatarData } from '@/lib/datas'
import {
  descreverRecorrencia,
  erroDoEditor,
  LETRAS_DIAS,
  NOMES_DIAS,
  regraDoEditor,
  trocarUnidade,
  type EstadoEditor,
  type Unidade,
} from '@/lib/recorrencia'
import { cn } from '@/lib/utils'

const UNIDADES: Record<Unidade, string> = {
  dias: 'dias',
  semanas: 'semanas',
  meses: 'meses',
  anos: 'anos',
}

type Props = {
  id: string
  valor: EstadoEditor
  /** A primeira data do item: pré-preenche dias e define o dia/mês da regra anual (RN-30). */
  primeiraData: string | null
  onChange: (estado: EstadoEditor) => void
  /** Mostra o que falta (só depois de tentar salvar). */
  mostrarErro?: boolean
}

/**
 * 01 §4.6: "A cada [N] [dias | semanas | meses | anos]", dias da semana, dia do mês e a frase
 * final com o texto de RN-35. Usado por tarefas repetidas e lembretes.
 */
export function EditorRecorrencia({ id, valor, primeiraData, onChange, mostrarErro }: Props) {
  const regra = regraDoEditor(valor, primeiraData)
  const erro = erroDoEditor(valor, primeiraData)
  const alternarDia = (dia: number) =>
    onChange({
      ...valor,
      diasSemana: valor.diasSemana.includes(dia)
        ? valor.diasSemana.filter((d) => d !== dia)
        : [...valor.diasSemana, dia],
    })

  return (
    <div id={id} role="group" aria-label="Repetição" className="grid gap-2 rounded-lg border p-3">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span>A cada</span>
        <Input
          type="number"
          min={1}
          max={365}
          aria-label="Intervalo"
          className="h-8 w-20"
          value={Number.isNaN(valor.intervalo) ? '' : valor.intervalo}
          onChange={(evento) => onChange({ ...valor, intervalo: evento.target.valueAsNumber })}
        />
        <Select
          value={valor.unidade}
          onValueChange={(unidade) =>
            onChange(trocarUnidade(valor, unidade as Unidade, primeiraData))
          }
        >
          <SelectTrigger size="sm" aria-label="Unidade">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(UNIDADES).map(([unidade, rotulo]) => (
              <SelectItem key={unidade} value={unidade}>
                {rotulo}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {valor.unidade === 'meses' && (
          <>
            <span>no dia</span>
            <Input
              type="number"
              min={1}
              max={31}
              aria-label="Dia do mês"
              className="h-8 w-20"
              value={valor.diaMes ?? ''}
              onChange={(evento) =>
                onChange({
                  ...valor,
                  diaMes: evento.target.value ? evento.target.valueAsNumber : null,
                })
              }
            />
          </>
        )}
        {valor.unidade === 'anos' && primeiraData && (
          <span className="text-muted-foreground">em {formatarData(primeiraData).slice(0, 5)}</span>
        )}
      </div>
      {valor.unidade === 'semanas' && (
        <div role="group" aria-label="Dias da semana" className="flex gap-1">
          {LETRAS_DIAS.map((letra, dia) => {
            const marcado = valor.diasSemana.includes(dia)
            return (
              <button
                key={dia}
                type="button"
                aria-pressed={marcado}
                aria-label={NOMES_DIAS[dia]}
                title={NOMES_DIAS[dia]}
                onClick={() => alternarDia(dia)}
                className={cn(
                  'size-8 rounded-full border text-xs font-medium outline-none focus-visible:ring-3 focus-visible:ring-ring/50',
                  marcado ? 'border-primary bg-primary text-primary-foreground' : 'bg-background',
                )}
              >
                {letra}
              </button>
            )
          })}
        </div>
      )}
      <p aria-live="polite" className={cn('text-sm', !regra && mostrarErro && 'text-destructive')}>
        {regra ? `Repete ${descreverRecorrencia(regra)}` : mostrarErro ? erro : ' '}
      </p>
    </div>
  )
}
