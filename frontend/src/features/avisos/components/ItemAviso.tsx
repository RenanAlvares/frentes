import { Bell, CircleCheck } from 'lucide-react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { ChipProjeto } from '@/components/comum/ChipProjeto'
import { Button } from '@/components/ui/button'
import type { Aviso } from '@/features/avisos/hooks/useAvisos'
import { useDarBaixa, useDesfazerBaixa } from '@/features/lembretes/hooks/useLembretes'
import { useConcluirTarefa, useDesfazerConclusao } from '@/features/tarefas/hooks/useTarefas'
import { textoRelativo } from '@/lib/datas'
import { avisarComDesfazer } from '@/lib/desfazer'

type Props = {
  aviso: Aviso
  /** RN-54: `true` tira o item do painel após a ação; `false` devolve (Desfazer). */
  onTratado: (tratado: boolean) => void
}

/** 01 §4.1: ícone do tipo, título, chip do projeto, texto de prazo e ações. */
export function ItemAviso({ aviso, onTratado }: Props) {
  const Icone = aviso.tipo === 'lembrete' ? Bell : CircleCheck
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg border bg-white p-3 text-sm shadow-xs transition-colors hover:border-foreground/25">
      <Icone
        className="size-4 shrink-0 text-muted-foreground"
        aria-label={aviso.tipo === 'lembrete' ? 'Lembrete' : 'Tarefa'}
      />
      <div className="grid min-w-0 flex-1 gap-0.5">
        <p className="font-medium break-words">{aviso.titulo}</p>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <ChipProjeto projeto={aviso.projeto} />
          <span className={corDoPrazo(aviso.dias_restantes)}>{textoDoPrazo(aviso)}</span>
        </div>
      </div>
      <div className="flex gap-1">
        {aviso.tipo === 'lembrete' ? (
          <AcoesLembrete aviso={aviso} onTratado={onTratado} />
        ) : (
          <AcoesTarefa aviso={aviso} onTratado={onTratado} />
        )}
      </div>
    </li>
  )
}

/** 01 §4.1: vermelho se vencido, âmbar se vence hoje ou amanhã, cinza nos demais. */
function corDoPrazo(diasRestantes: number) {
  if (diasRestantes < 0) return 'font-medium text-red-600'
  if (diasRestantes <= 1) return 'text-amber-600'
  return 'text-muted-foreground'
}

function textoDoPrazo(aviso: Aviso) {
  if (aviso.meta) {
    return `${aviso.meta.feitas}/${aviso.meta.meta} · ${textoFimDoMes(aviso.dias_restantes)}`
  }
  // RN-34: só mostra a partir de 2 ocorrências perdidas.
  const ocorrencias = aviso.ocorrencias_atrasadas
  return (
    textoRelativo(aviso.dias_restantes) + (ocorrencias >= 2 ? ` · ${ocorrencias} ocorrências` : '')
  )
}

function textoFimDoMes(diasRestantes: number) {
  if (diasRestantes === 0) return 'mês termina hoje'
  if (diasRestantes === 1) return 'mês termina amanhã'
  return `mês termina em ${diasRestantes} dias`
}

type PropsAcoes = Props

/**
 * Ação + Desfazer (RN-54). `mutateAsync` (e não os callbacks do `mutate`) porque o item pode
 * sair da lista antes da resposta, e o toast precisa aparecer mesmo assim.
 */
async function executar(
  acao: () => Promise<unknown>,
  desfazer: () => Promise<unknown>,
  texto: string,
  onTratado: Props['onTratado'],
) {
  try {
    await acao()
  } catch (erro) {
    toast.error(mensagemDoErro(erro))
    return
  }
  onTratado(true)
  avisarComDesfazer(texto, () => desfazer().then(() => onTratado(false)))
}

function AcoesLembrete({ aviso, onTratado }: PropsAcoes) {
  const baixa = useDarBaixa(aviso.projeto.id)
  const desfazer = useDesfazerBaixa(aviso.projeto.id)
  const darBaixa = () =>
    executar(
      () => baixa.mutateAsync(aviso.id),
      () => desfazer.mutateAsync(aviso.id),
      'Baixa registrada',
      onTratado,
    )
  return (
    <>
      <Button
        size="sm"
        variant="outline"
        carregando={baixa.isPending}
        onClick={() => void darBaixa()}
      >
        Dar baixa
      </Button>
      <Button size="sm" variant="ghost" asChild>
        <Link to={`/projetos/${aviso.projeto.id}`}>Abrir projeto</Link>
      </Button>
    </>
  )
}

function AcoesTarefa({ aviso, onTratado }: PropsAcoes) {
  const concluir = useConcluirTarefa(aviso.projeto.id)
  const desfazer = useDesfazerConclusao(aviso.projeto.id)
  // Meta mensal: "+1" é o mesmo `concluir` (RN-24); o Desfazer apaga a execução (RN-26).
  const meta = aviso.meta !== null
  const agir = () =>
    executar(
      () => concluir.mutateAsync(aviso.id),
      () => desfazer.mutateAsync(aviso.id),
      meta ? '+1 registrado' : 'Tarefa concluída',
      onTratado,
    )
  return (
    <>
      <Button
        size="sm"
        variant="outline"
        carregando={concluir.isPending}
        onClick={() => void agir()}
      >
        {meta ? '+1' : 'Concluir'}
      </Button>
      <Button size="sm" variant="ghost" asChild>
        <Link to={`/projetos/${aviso.projeto.id}?tarefa=${aviso.id}`}>Abrir</Link>
      </Button>
    </>
  )
}
