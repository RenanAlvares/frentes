import { CalendarDays, X } from 'lucide-react'
import { useState } from 'react'
import { ptBR } from 'react-day-picker/locale'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { dataLocalParaIso, formatarData, isoParaDataLocal } from '@/lib/datas'

type Props = {
  id?: string
  valor: string | null
  onChange: (valor: string | null) => void
  invalido?: boolean
  descricaoId?: string
}

/** Data opcional "AAAA-MM-DD" escolhida no calendário (05 §6). */
export function CampoData({ id, valor, onChange, invalido, descricaoId }: Props) {
  const [aberto, setAberto] = useState(false)

  return (
    <div className="flex items-center gap-1">
      <Popover open={aberto} onOpenChange={setAberto}>
        <PopoverTrigger asChild>
          <Button
            id={id}
            type="button"
            variant="outline"
            aria-invalid={invalido}
            aria-describedby={descricaoId}
            className="flex-1 justify-start font-normal"
          >
            <CalendarDays />
            {valor ? (
              formatarData(valor)
            ) : (
              <span className="text-muted-foreground">Selecionar data</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            locale={ptBR}
            selected={valor ? isoParaDataLocal(valor) : undefined}
            defaultMonth={valor ? isoParaDataLocal(valor) : undefined}
            onSelect={(data) => {
              onChange(data ? dataLocalParaIso(data) : null)
              setAberto(false)
            }}
          />
        </PopoverContent>
      </Popover>
      {valor && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Limpar data"
          onClick={() => onChange(null)}
        >
          <X />
        </Button>
      )}
    </div>
  )
}
