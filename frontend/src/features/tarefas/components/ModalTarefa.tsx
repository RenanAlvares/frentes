import { CheckCheck, Plus, Trash2 } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'
import { ErroApi, mensagemDoErro } from '@/api/erros'
import { ConfirmarDescartar } from '@/components/comum/ConfirmarDescartar'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { FormularioTarefa } from '@/features/tarefas/components/FormularioTarefa'
import { ResumoTarefa } from '@/features/tarefas/components/ResumoTarefa'
import {
  corpoAtualizar,
  corpoCriar,
  TAREFA_VAZIA,
  valoresDaTarefa,
  type Sujos,
  type ValoresTarefa,
} from '@/features/tarefas/formulario'
import {
  avisarComDesfazer,
  useAtualizarTarefa,
  useConcluirTarefa,
  useCriarTarefa,
  useDesfazerConclusao,
  useExcluirTarefa,
  useRestaurarTarefa,
  useTarefa,
} from '@/features/tarefas/hooks/useTarefas'

type Props = {
  projetoId: string
  aberto: boolean
  /** Ausente = criar ("Mais opções"); presente = a tarefa de `?tarefa=`. */
  tarefaId?: string
  onFechar: () => void
}

/** 01 §4.5 e RN-85: Salvar grava a edição; Concluir e Excluir agem na hora, com Desfazer. */
export function ModalTarefa({ projetoId, aberto, tarefaId, onFechar }: Props) {
  const edicao = tarefaId !== undefined
  const { data: tarefa, isError, error } = useTarefa(aberto ? tarefaId : undefined)
  const criar = useCriarTarefa(projetoId)
  const atualizar = useAtualizarTarefa(projetoId)
  const concluir = useConcluirTarefa(projetoId)
  const desfazer = useDesfazerConclusao(projetoId)
  const excluir = useExcluirTarefa(projetoId)
  const restaurar = useRestaurarTarefa(projetoId)
  const sujo = useRef(false)
  // O que fazer se o usuário confirmar o descarte: só fechar, ou concluir/excluir.
  const [aposDescartar, setAposDescartar] = useState<(() => void) | null>(null)

  const marcarSujo = useCallback((valor: boolean) => {
    sujo.current = valor
  }, [])

  function fechar() {
    sujo.current = false
    setAposDescartar(null)
    onFechar()
  }

  /** Com alterações não salvas, pergunta antes (RN-85). */
  function confirmandoDescarte(acao: () => void) {
    if (sujo.current) setAposDescartar(() => acao)
    else acao()
  }

  async function salvar(valores: ValoresTarefa, sujos: Sujos) {
    if (!edicao) {
      await criar.mutateAsync(corpoCriar(valores))
    } else {
      const corpo = corpoAtualizar(valores, sujos)
      if (Object.keys(corpo).length > 0) await atualizar.mutateAsync({ id: tarefaId, dados: corpo })
    }
    fechar()
  }

  /** Meta "+1": o modal continua aberto e o resumo do mês se atualiza. */
  function maisUm(id: string) {
    concluir.mutate(id, { onError: (erro) => toast.error(mensagemDoErro(erro)) })
  }

  function concluirTarefa(id: string) {
    concluir.mutate(id, {
      onSuccess: () => {
        fechar()
        avisarComDesfazer('Tarefa concluída', () => desfazer.mutateAsync(id))
      },
      onError: (erro) => toast.error(mensagemDoErro(erro)),
    })
  }

  function excluirTarefa(id: string) {
    excluir.mutate(id, {
      onSuccess: () => {
        fechar()
        avisarComDesfazer('Movido para a lixeira', () => restaurar.mutateAsync(id))
      },
      onError: (erro) => toast.error(mensagemDoErro(erro)),
    })
  }

  let conteudo
  if (!edicao) {
    conteudo = (
      <FormularioTarefa
        inicial={TAREFA_VAZIA}
        edicao={false}
        onSalvar={salvar}
        onSujoChange={marcarSujo}
      />
    )
  } else if (isError) {
    conteudo = (
      <p role="alert" className="text-sm text-destructive">
        {error instanceof ErroApi && error.status === 404
          ? 'Tarefa não encontrada.'
          : mensagemDoErro(error)}
      </p>
    )
  } else if (!tarefa) {
    conteudo = <Skeleton className="h-72 w-full" />
  } else {
    const meta = tarefa.tipo === 'meta_mensal'
    conteudo = (
      <div className="grid gap-4">
        <ResumoTarefa tarefa={tarefa} />
        <FormularioTarefa
          inicial={valoresDaTarefa(tarefa)}
          edicao
          onSalvar={salvar}
          onSujoChange={marcarSujo}
          acoesEsquerda={
            <Button
              type="button"
              variant="ghost"
              className="text-destructive"
              onClick={() => confirmandoDescarte(() => excluirTarefa(tarefa.id))}
            >
              <Trash2 /> Excluir
            </Button>
          }
          acoesDireita={
            meta ? (
              <Button type="button" variant="outline" onClick={() => maisUm(tarefa.id)}>
                <Plus /> +1
              </Button>
            ) : (
              tarefa.status !== 'concluida' && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => confirmandoDescarte(() => concluirTarefa(tarefa.id))}
                >
                  <CheckCheck /> Concluir
                </Button>
              )
            )
          }
        />
      </div>
    )
  }

  return (
    <>
      <Dialog open={aberto} onOpenChange={(abrir) => !abrir && confirmandoDescarte(fechar)}>
        <DialogContent aria-describedby={undefined} className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>{edicao ? 'Tarefa' : 'Nova tarefa'}</DialogTitle>
          </DialogHeader>
          {conteudo}
        </DialogContent>
      </Dialog>
      <ConfirmarDescartar
        aberto={aposDescartar !== null}
        onContinuar={() => setAposDescartar(null)}
        onDescartar={() => {
          const acao = aposDescartar
          sujo.current = false
          setAposDescartar(null)
          acao?.()
        }}
      />
    </>
  )
}
