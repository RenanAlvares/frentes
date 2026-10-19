import { useRef, useState, type FormEvent } from 'react'
import { toast } from 'sonner'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCriarTarefa } from '@/features/tarefas/hooks/useTarefas'
import { useAtalho } from '@/lib/atalhos'

type Props = {
  projetoId: string
  /** "Mais opções": abre o modal completo de criação. */
  onMaisOpcoes: () => void
}

/** 01 §4.4: título + Enter cria uma tarefa simples em Pendente, prioridade média. */
export function CriacaoRapida({ projetoId, onMaisOpcoes }: Props) {
  const criar = useCriarTarefa(projetoId)
  const [titulo, setTitulo] = useState('')
  const [erro, setErro] = useState<string>()
  const campo = useRef<HTMLInputElement>(null)
  // RN-130: `N` = nova tarefa (foca este campo).
  useAtalho('n', () => campo.current?.focus())

  function enviar(evento: FormEvent) {
    evento.preventDefault()
    const limpo = titulo.trim()
    if (!limpo || criar.isPending) return
    criar.mutate(
      { titulo: limpo },
      {
        onSuccess: () => {
          setTitulo('')
          setErro(undefined)
        },
        onError: (falha) => {
          const doCampo = camposDoErro(falha).titulo
          if (doCampo) setErro(doCampo)
          else toast.error(mensagemDoErro(falha))
        },
      },
    )
  }

  return (
    <form onSubmit={enviar} className="grid gap-1">
      <div className="flex gap-2">
        <Input
          ref={campo}
          aria-label="Nova tarefa"
          placeholder="Nova tarefa (Enter para criar)"
          value={titulo}
          onChange={(evento) => setTitulo(evento.target.value)}
          aria-invalid={Boolean(erro)}
          aria-describedby={erro ? 'nova-tarefa-erro' : undefined}
        />
        <Button type="button" variant="outline" onClick={onMaisOpcoes}>
          Mais opções
        </Button>
      </div>
      {erro && (
        <p id="nova-tarefa-erro" className="text-sm text-destructive">
          {erro}
        </p>
      )}
    </form>
  )
}
