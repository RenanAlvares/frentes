import { Bell, CircleCheck, Target } from 'lucide-react'
import { createElement, type ReactNode } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { useSaude } from '@/app/layout/useSaude'
import { ChipProjeto } from '@/components/comum/ChipProjeto'
import { Button } from '@/components/ui/button'
import type { Aviso } from '@/features/avisos/hooks/useAvisos'
import { useDarBaixa, useDesfazerBaixa } from '@/features/lembretes/hooks/useLembretes'
import { useConcluirTarefa, useDesfazerConclusao } from '@/features/tarefas/hooks/useTarefas'
import { anoDe, formatarData, formatarDataCurta, textoRelativo } from '@/lib/datas'
import { avisarComDesfazer } from '@/lib/desfazer'
import { cn } from '@/lib/utils'

type Props = {
  aviso: Aviso
  /** RN-54: `true` tira o item do painel após a ação; `false` devolve (Desfazer). */
  onTratado: (tratado: boolean) => void
}

const TIPOS = {
  lembrete: { rotulo: 'Lembrete', icone: Bell, cor: 'bg-amber-100 text-amber-800' },
  tarefa: { rotulo: 'Tarefa', icone: CircleCheck, cor: 'bg-blue-100 text-blue-800' },
  meta: { rotulo: 'Meta mensal', icone: Target, cor: 'bg-blue-100 text-blue-800' },
} as const

/**
 * 01 §4.1: tipo (rótulo e ícone), título, projeto, data (ou progresso da meta), texto relativo
 * e ações. A borda esquerda mostra a urgência.
 */
export function ItemAviso({ aviso, onTratado }: Props) {
  const { data: saude } = useSaude()
  const tipo = TIPOS[aviso.meta ? 'meta' : aviso.tipo]
  const data = saude
    ? formatarDataCurta(aviso.vencimento, anoDe(saude.hoje))
    : formatarData(aviso.vencimento)
  return (
    <li
      className={cn(
        'flex flex-wrap items-center gap-x-4 gap-y-3 rounded-lg border border-l-4 bg-white p-3 text-sm shadow-xs transition-shadow hover:shadow-md',
        bordaDaUrgencia(aviso.dias_restantes),
      )}
    >
      <div className="flex min-w-0 flex-1 items-start gap-3">
        <span
          aria-hidden
          className={cn('flex size-8 shrink-0 items-center justify-center rounded-full', tipo.cor)}
        >
          {createElement(tipo.icone, { className: 'size-4' })}
        </span>
        <div className="grid min-w-0 gap-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                'rounded px-1.5 py-0.5 text-[11px] font-semibold tracking-wide uppercase',
                tipo.cor,
              )}
            >
              {tipo.rotulo}
            </span>
            <p className="font-semibold break-words">{aviso.titulo}</p>
          </div>
          <dl className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
            <Campo rotulo="Projeto">
              <ChipProjeto projeto={aviso.projeto} />
            </Campo>
            {aviso.meta ? (
              <Campo rotulo="Meta">
                {aviso.meta.feitas}/{aviso.meta.meta} no mês
              </Campo>
            ) : (
              <Campo rotulo={aviso.tipo === 'lembrete' ? 'Vencimento' : 'Prazo'}>{data}</Campo>
            )}
            <div>
              <dt className="sr-only">Situação</dt>
              <dd className={corDoPrazo(aviso.dias_restantes)}>{textoDoPrazo(aviso)}</dd>
            </div>
          </dl>
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

function Campo({ rotulo, children }: { rotulo: string; children: ReactNode }) {
  return (
    <div className="flex items-center gap-1.5">
      <dt className="text-muted-foreground">{rotulo}</dt>
      <dd className="font-medium">{children}</dd>
    </div>
  )
}

/** 01 §4.1: vermelho se vencido, âmbar se vence hoje ou amanhã, cinza nos demais. */
function corDoPrazo(diasRestantes: number) {
  if (diasRestantes < 0) return 'font-semibold text-red-600'
  if (diasRestantes <= 1) return 'font-semibold text-amber-600'
  return 'text-muted-foreground'
}

/** A mesma urgência, na borda esquerda do item. */
function bordaDaUrgencia(diasRestantes: number) {
  if (diasRestantes < 0) return 'border-l-red-500'
  if (diasRestantes <= 1) return 'border-l-amber-500'
  return 'border-l-sky-400'
}

function textoDoPrazo(aviso: Aviso) {
  if (aviso.meta) return textoFimDoMes(aviso.dias_restantes)
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
