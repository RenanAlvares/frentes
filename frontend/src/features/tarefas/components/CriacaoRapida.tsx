import { useState, type FormEvent } from 'react'
import { toast } from 'sonner'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { Input } from '@/components/ui/input'
import { useCriarTarefa } from '@/features/tarefas/hooks/useTarefas'

/** 01 §4.4: título + Enter cria uma tarefa simples em Pendente, prioridade média. */
export function CriacaoRapida({ projetoId }: { projetoId: string }) {
  const criar = useCriarTarefa(projetoId)
  const [titulo, setTitulo] = useState('')
  const [erro, setErro] = useState<string>()

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
      <Input
        aria-label="Nova tarefa"
        placeholder="Nova tarefa (Enter para criar)"
        value={titulo}
        onChange={(evento) => setTitulo(evento.target.value)}
        aria-invalid={Boolean(erro)}
        aria-describedby={erro ? 'nova-tarefa-erro' : undefined}
      />
      {erro && (
        <p id="nova-tarefa-erro" className="text-sm text-destructive">
          {erro}
        </p>
      )}
    </form>
  )
}
