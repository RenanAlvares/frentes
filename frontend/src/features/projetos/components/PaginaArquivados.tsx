import { Archive } from 'lucide-react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { mensagemDoErro } from '@/api/erros'
import { EstadoVazio } from '@/components/comum/EstadoVazio'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAtualizarProjeto, useProjetos } from '@/features/projetos/hooks/useProjetos'
import { CORES_PROJETO } from '@/lib/cores'
import { formatarCarimbo } from '@/lib/datas'
import { cn } from '@/lib/utils'

/** 01 §4.7: projetos concluídos (RN-12), com Abrir e Reabrir. */
export function PaginaArquivados() {
  const { data: projetos, isPending, isError, error } = useProjetos(true)
  const atualizar = useAtualizarProjeto()

  function reabrir(id: string) {
    // RN-12: reabrir volta para Em andamento; o projeto sai desta lista e volta à home.
    atualizar.mutate(
      { id, dados: { status: 'em_andamento' } },
      { onError: (erro) => toast.error(mensagemDoErro(erro)) },
    )
  }

  return (
    <section className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Arquivados</h1>
      {isPending ? (
        <Skeleton className="h-32 rounded-xl" />
      ) : isError ? (
        <p role="alert" className="text-destructive">
          {mensagemDoErro(error)}
        </p>
      ) : projetos.length === 0 ? (
        <EstadoVazio icone={Archive} titulo="Nenhum projeto arquivado" />
      ) : (
        <ul className="divide-y rounded-xl border bg-white shadow-sm">
          {projetos.map((projeto) => (
            <li key={projeto.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
              <span
                aria-hidden
                className={cn('size-3 shrink-0 rounded-full', CORES_PROJETO[projeto.cor].fundo)}
              />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{projeto.nome}</p>
                <p className="text-sm text-muted-foreground">
                  Concluído em {formatarCarimbo(projeto.atualizado_em)}
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" asChild>
                  <Link to={`/projetos/${projeto.id}`} aria-label={`Abrir ${projeto.nome}`}>
                    Abrir
                  </Link>
                </Button>
                <Button
                  size="sm"
                  aria-label={`Reabrir ${projeto.nome}`}
                  carregando={atualizar.isPending && atualizar.variables.id === projeto.id}
                  onClick={() => reabrir(projeto.id)}
                >
                  Reabrir
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
