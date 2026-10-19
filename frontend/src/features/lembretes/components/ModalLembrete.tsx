import { useCallback, useRef, useState } from 'react'
import { ConfirmarDescartar } from '@/components/comum/ConfirmarDescartar'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { FormularioLembrete } from '@/features/lembretes/components/FormularioLembrete'
import {
  corpoAtualizarLembrete,
  corpoCriarLembrete,
  LEMBRETE_VAZIO,
  valoresDoLembrete,
  type Lembrete,
  type SujosLembrete,
  type ValoresLembrete,
} from '@/features/lembretes/formulario'
import { useAtualizarLembrete, useCriarLembrete } from '@/features/lembretes/hooks/useLembretes'

type Props = {
  projetoId: string
  aberto: boolean
  /** Ausente = criar ("+ Lembrete"); presente = editar este lembrete. */
  lembrete?: Lembrete
  onFechar: () => void
}

/** 01 §4.6 e RN-85: Salvar grava; fechar com alterações pede confirmação. */
export function ModalLembrete({ projetoId, aberto, lembrete, onFechar }: Props) {
  const criar = useCriarLembrete(projetoId)
  const atualizar = useAtualizarLembrete(projetoId)
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

  async function salvar(valores: ValoresLembrete, sujos: SujosLembrete) {
    if (!lembrete) {
      await criar.mutateAsync(corpoCriarLembrete(valores))
    } else {
      const corpo = corpoAtualizarLembrete(valores, sujos)
      if (Object.keys(corpo).length > 0) {
        await atualizar.mutateAsync({ id: lembrete.id, dados: corpo })
      }
    }
    fechar()
  }

  return (
    <>
      <Dialog
        open={aberto}
        onOpenChange={(abrir) => !abrir && (sujo.current ? setConfirmando(true) : fechar())}
      >
        <DialogContent aria-describedby={undefined} className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{lembrete ? 'Editar lembrete' : 'Novo lembrete'}</DialogTitle>
          </DialogHeader>
          <FormularioLembrete
            inicial={lembrete ? valoresDoLembrete(lembrete) : LEMBRETE_VAZIO}
            edicao={lembrete !== undefined}
            onSalvar={salvar}
            onSujoChange={marcarSujo}
          />
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
