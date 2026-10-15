import { useCallback, useRef, useState } from 'react'
import { ConfirmarDescartar } from '@/components/comum/ConfirmarDescartar'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { FormularioProjeto } from '@/features/projetos/components/FormularioProjeto'
import {
  PROJETO_VAZIO,
  valoresDoProjeto,
  type ValoresProjeto,
} from '@/features/projetos/formulario'
import {
  useAtualizarProjeto,
  useCriarProjeto,
  useProjeto,
} from '@/features/projetos/hooks/useProjetos'

type Props = {
  aberto: boolean
  /** Ausente = criar; presente = editar esse projeto. */
  projetoId?: string
  onFechar: () => void
}

/** 01 §4.6 (Projeto) e RN-85: salva com o botão Salvar; fechar sujo pede confirmação. */
export function ModalProjeto({ aberto, projetoId, onFechar }: Props) {
  const edicao = projetoId !== undefined
  const { data: projeto } = useProjeto(aberto ? projetoId : undefined)
  const criar = useCriarProjeto()
  const atualizar = useAtualizarProjeto()
  const sujo = useRef(false)
  const [confirmando, setConfirmando] = useState(false)

  const marcarSujo = useCallback((valor: boolean) => {
    sujo.current = valor
  }, [])

  function fechar() {
    sujo.current = false
    setConfirmando(false)
    onFechar()
  }

  function pedirFechamento() {
    if (sujo.current) setConfirmando(true)
    else fechar()
  }

  async function salvar(valores: ValoresProjeto, alterados: Partial<ValoresProjeto>) {
    if (!edicao) {
      await criar.mutateAsync(valores)
    } else if (Object.keys(alterados).length > 0) {
      await atualizar.mutateAsync({ id: projetoId, dados: alterados })
    }
    fechar()
  }

  return (
    <>
      <Dialog open={aberto} onOpenChange={(abrir) => !abrir && pedirFechamento()}>
        <DialogContent aria-describedby={undefined} className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{edicao ? 'Editar projeto' : 'Novo projeto'}</DialogTitle>
          </DialogHeader>
          {edicao && !projeto ? (
            <Skeleton className="h-80 w-full" />
          ) : (
            <FormularioProjeto
              inicial={projeto ? valoresDoProjeto(projeto) : PROJETO_VAZIO}
              onSalvar={salvar}
              onCancelar={pedirFechamento}
              onSujoChange={marcarSujo}
            />
          )}
        </DialogContent>
      </Dialog>
      <ConfirmarDescartar
        aberto={confirmando}
        onContinuar={() => setConfirmando(false)}
        onDescartar={fechar}
      />
    </>
  )
}
