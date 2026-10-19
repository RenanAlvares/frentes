import { Trash2 } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { ConfirmarDescartar } from '@/components/comum/ConfirmarDescartar'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { FormularioAnotacao } from '@/features/anotacoes/components/FormularioAnotacao'
import {
  ANOTACAO_VAZIA,
  corpoAtualizarAnotacao,
  valoresDaAnotacao,
  type Anotacao,
  type SujosAnotacao,
  type ValoresAnotacao,
} from '@/features/anotacoes/formulario'
import {
  useAtualizarAnotacao,
  useCriarAnotacao,
  useExcluirAnotacao,
  useRestaurarAnotacao,
} from '@/features/anotacoes/hooks/useAnotacoes'
import { avisarComDesfazer } from '@/lib/desfazer'

type Props = {
  projetoId: string
  aberto: boolean
  /** Ausente = criar ("+ Anotação"); presente = editar esta anotação. */
  anotacao?: Anotacao
  onFechar: () => void
}

/** 01 §4.6 e RN-85: Salvar grava; fechar com alterações pede confirmação; Excluir tem Desfazer. */
export function ModalAnotacao({ projetoId, aberto, anotacao, onFechar }: Props) {
  const criar = useCriarAnotacao(projetoId)
  const atualizar = useAtualizarAnotacao(projetoId)
  const excluir = useExcluirAnotacao(projetoId)
  const restaurar = useRestaurarAnotacao(projetoId)
  const sujo = useRef(false)
  // O que fazer se o usuário confirmar o descarte: só fechar, ou excluir.
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

  async function salvar(valores: ValoresAnotacao, sujos: SujosAnotacao) {
    if (!anotacao) {
      await criar.mutateAsync(valores)
    } else {
      const corpo = corpoAtualizarAnotacao(valores, sujos)
      if (Object.keys(corpo).length > 0)
        await atualizar.mutateAsync({ id: anotacao.id, dados: corpo })
    }
    fechar()
  }

  function excluirAnotacao(id: string) {
    excluir.mutate(id, {
      onSuccess: () => {
        fechar()
        avisarComDesfazer('Movido para a lixeira', () => restaurar.mutateAsync(id))
      },
      onError: (erro) => toast.error(mensagemDoErro(erro)),
    })
  }

  return (
    <>
      <Dialog open={aberto} onOpenChange={(abrir) => !abrir && confirmandoDescarte(fechar)}>
        <DialogContent aria-describedby={undefined} className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{anotacao ? 'Editar anotação' : 'Nova anotação'}</DialogTitle>
          </DialogHeader>
          <FormularioAnotacao
            inicial={anotacao ? valoresDaAnotacao(anotacao) : ANOTACAO_VAZIA}
            onSalvar={salvar}
            onSujoChange={marcarSujo}
            acoesEsquerda={
              anotacao && (
                <Button
                  type="button"
                  variant="ghost"
                  className="text-destructive"
                  carregando={excluir.isPending}
                  onClick={() => confirmandoDescarte(() => excluirAnotacao(anotacao.id))}
                >
                  <Trash2 /> Excluir
                </Button>
              )
            }
          />
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
