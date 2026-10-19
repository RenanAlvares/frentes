import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'

/** Toast com Desfazer por 6 s (01 §5); erro ao desfazer vira toast com a mensagem da API. */
export function avisarComDesfazer(texto: string, desfazer: () => Promise<unknown>) {
  toast(texto, {
    duration: 6000,
    action: {
      label: 'Desfazer',
      onClick: () => void desfazer().catch((erro: unknown) => toast.error(mensagemDoErro(erro))),
    },
  })
}
