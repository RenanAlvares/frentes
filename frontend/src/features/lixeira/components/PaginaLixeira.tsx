import {
  Bell,
  FileText,
  FolderKanban,
  type LucideIcon,
  RotateCcw,
  SquareCheck,
  StickyNote,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { useSaude } from '@/app/layout/useSaude'
import { EstadoVazio } from '@/components/comum/EstadoVazio'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  type ItemLixeira,
  type TipoItemLixeira,
  useEsvaziarLixeira,
  useExcluirDaLixeira,
  useLixeira,
  useRestaurarDaLixeira,
} from '@/features/lixeira/hooks/useLixeira'
import { formatarCarimbo } from '@/lib/datas'

const TIPOS: Record<TipoItemLixeira, { rotulo: string; icone: LucideIcon }> = {
  projeto: { rotulo: 'Projeto', icone: FolderKanban },
  tarefa: { rotulo: 'Tarefa', icone: SquareCheck },
  lembrete: { rotulo: 'Lembrete', icone: Bell },
  documento: { rotulo: 'Documento', icone: FileText },
  anotacao: { rotulo: 'Anotação', icone: StickyNote },
}

/** RN-94: `dias_para_expirar` vem da API (o front não conta dias). */
function textoExpiracao(dias: number) {
  if (dias === 0) return 'apagado definitivamente na próxima vez que o app abrir'
  return `apagado definitivamente em ${dias} ${dias === 1 ? 'dia' : 'dias'}`
}

type Confirmacao = { titulo: string; descricao: string; acao: string; executar: () => void }

/** Lixeira (01 §4.8; RN-90..94). */
export function PaginaLixeira() {
  const { data: itens, isPending, isError, error } = useLixeira()
  const { data: saude } = useSaude()
  const esvaziar = useEsvaziarLixeira()
  const excluir = useExcluirDaLixeira()
  const [confirmacao, setConfirmacao] = useState<Confirmacao | null>(null)
  const avisarErro = { onError: (erro: unknown) => toast.error(mensagemDoErro(erro)) }

  // Ações irreversíveis (RN-93) sempre pedem confirmação.
  function confirmarExclusao(item: ItemLixeira) {
    setConfirmacao({
      titulo: 'Excluir definitivamente?',
      descricao: `“${item.titulo}” será apagado de vez. Não dá para desfazer.`,
      acao: 'Excluir',
      executar: () => excluir.mutate({ tipo: item.tipo, id: item.id }, avisarErro),
    })
  }

  function confirmarEsvaziar(total: number) {
    setConfirmacao({
      titulo: 'Esvaziar lixeira?',
      descricao: `${total === 1 ? 'O item será apagado' : `Os ${total} itens serão apagados`} de vez. Não dá para desfazer.`,
      acao: 'Esvaziar',
      executar: () => esvaziar.mutate(undefined, avisarErro),
    })
  }

  let conteudo
  if (isPending) {
    conteudo = (
      <div className="grid gap-2">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-16 rounded-lg" />
        ))}
      </div>
    )
  } else if (isError) {
    conteudo = (
      <p role="alert" className="text-sm text-destructive">
        {mensagemDoErro(error)}
      </p>
    )
  } else if (itens.length === 0) {
    conteudo = <EstadoVazio icone={Trash2} titulo="A lixeira está vazia." />
  } else {
    conteudo = (
      <ul className="grid gap-2">
        {itens.map((item) => (
          <LinhaLixeira
            key={`${item.tipo}:${item.id}`}
            item={item}
            onExcluir={() => confirmarExclusao(item)}
          />
        ))}
      </ul>
    )
  }

  return (
    <div className="mx-auto grid max-w-3xl gap-4">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold">Lixeira</h1>
        {itens && itens.length > 0 && (
          <Button
            variant="outline"
            className="ml-auto text-destructive"
            carregando={esvaziar.isPending}
            onClick={() => confirmarEsvaziar(itens.length)}
          >
            <Trash2 /> Esvaziar lixeira
          </Button>
        )}
      </div>
      {saude && (
        <p className="rounded-lg border bg-white px-3 py-2 text-sm text-muted-foreground shadow-xs">
          Itens ficam aqui por {saude.lixeira_dias} dias.
        </p>
      )}
      {conteudo}
      <AlertDialog
        open={confirmacao !== null}
        onOpenChange={(abrir) => !abrir && setConfirmacao(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmacao?.titulo}</AlertDialogTitle>
            <AlertDialogDescription>{confirmacao?.descricao}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={() => confirmacao?.executar()}>
              {confirmacao?.acao}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

/** 01 §4.8: tipo, nome, projeto de origem, excluído em e quando será apagado de vez. */
function LinhaLixeira({ item, onExcluir }: { item: ItemLixeira; onExcluir: () => void }) {
  const restaurar = useRestaurarDaLixeira()
  const { rotulo, icone: Icone } = TIPOS[item.tipo]
  return (
    <li className="flex flex-wrap items-center gap-3 rounded-lg border bg-white p-3 text-sm shadow-xs">
      <Icone className="size-4 shrink-0 text-muted-foreground" aria-hidden />
      <div className="grid min-w-0 flex-1 gap-0.5">
        <p className="font-medium break-words">{item.titulo}</p>
        <p className="text-xs text-muted-foreground">
          {rotulo}
          {item.projeto_nome && ` · ${item.projeto_nome}`} · excluído em{' '}
          {formatarCarimbo(item.excluido_em)} · {textoExpiracao(item.dias_para_expirar)}
        </p>
      </div>
      <div className="flex gap-1">
        <Button
          size="sm"
          variant="outline"
          carregando={restaurar.isPending}
          onClick={() =>
            restaurar.mutate(
              { tipo: item.tipo, id: item.id },
              { onError: (erro) => toast.error(mensagemDoErro(erro)) },
            )
          }
        >
          <RotateCcw /> Restaurar
        </Button>
        <Button size="sm" variant="ghost" className="text-destructive" onClick={onExcluir}>
          Excluir agora
        </Button>
      </div>
    </li>
  )
}
