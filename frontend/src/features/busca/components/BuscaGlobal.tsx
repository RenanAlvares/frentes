import {
  Bell,
  FileText,
  FolderKanban,
  type LucideIcon,
  Search,
  SquareCheck,
  StickyNote,
} from 'lucide-react'
import { type ReactNode, useEffect, useState } from 'react'
import { Link } from 'react-router'
import { mensagemDoErro } from '@/api/erros'
import { ChipProjeto } from '@/components/comum/ChipProjeto'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import {
  type ItemBusca,
  MINIMO_BUSCA,
  type ResultadoBusca,
  useAtrasado,
  useBusca,
} from '@/features/busca/hooks/useBusca'
import { useAtalho } from '@/lib/atalhos'

type Grupo = keyof ResultadoBusca

const GRUPOS: { grupo: Grupo; rotulo: string; icone: LucideIcon }[] = [
  { grupo: 'projetos', rotulo: 'Projetos', icone: FolderKanban },
  { grupo: 'tarefas', rotulo: 'Tarefas', icone: SquareCheck },
  { grupo: 'lembretes', rotulo: 'Lembretes', icone: Bell },
  { grupo: 'anotacoes', rotulo: 'Anotações', icone: StickyNote },
  { grupo: 'documentos', rotulo: 'Documentos', icone: FileText },
]

/** Para onde cada resultado leva: o projeto, ou o modal da tarefa (`?tarefa=`, 01 §3). */
function destino(grupo: Grupo, item: ItemBusca) {
  if (grupo === 'projetos') return `/projetos/${item.id}`
  if (grupo === 'tarefas') return `/projetos/${item.projeto.id}?tarefa=${item.id}`
  return `/projetos/${item.projeto.id}`
}

/** Busca global do cabeçalho (01 §3; RN-120..121). `/` ou `Ctrl+K` abre (RN-130). */
export function BuscaGlobal() {
  const [aberta, setAberta] = useState(false)
  const [termo, setTermo] = useState('')
  const atrasado = useAtrasado(termo, 250)
  const { data, isError, error } = useBusca(atrasado)

  useEffect(() => {
    function atalho(evento: KeyboardEvent) {
      if ((evento.ctrlKey || evento.metaKey) && evento.key.toLowerCase() === 'k') {
        evento.preventDefault()
        setAberta(true)
      }
    }
    window.addEventListener('keydown', atalho)
    return () => window.removeEventListener('keydown', atalho)
  }, [])
  // `/` é atalho de uma tecla: não vale com o foco num campo de texto.
  useAtalho('/', () => setAberta(true))

  function alternar(abrir: boolean) {
    setAberta(abrir)
    if (!abrir) setTermo('')
  }

  const curto = atrasado.trim().length < MINIMO_BUSCA
  const vazio = data !== undefined && GRUPOS.every(({ grupo }) => data[grupo].length === 0)
  let conteudo
  if (termo.trim().length < MINIMO_BUSCA) {
    conteudo = <Aviso>Digite pelo menos {MINIMO_BUSCA} letras.</Aviso>
  } else if (isError) {
    conteudo = <Aviso>{mensagemDoErro(error)}</Aviso>
  } else if (curto || data === undefined) {
    // Esperando o atraso da digitação ou a primeira resposta.
    conteudo = <Aviso>Buscando…</Aviso>
  } else if (vazio) {
    conteudo = <Aviso>Nada encontrado para “{atrasado.trim()}”.</Aviso>
  } else {
    conteudo = (
      <div className="grid max-h-[60vh] gap-3 overflow-y-auto">
        {GRUPOS.filter(({ grupo }) => data[grupo].length > 0).map(
          ({ grupo, rotulo, icone: Icone }) => (
            <section key={grupo} aria-label={rotulo} className="grid gap-1">
              <h3 className="px-2 text-xs font-semibold text-muted-foreground uppercase">
                {rotulo}
              </h3>
              <ul className="grid">
                {data[grupo].map((item) => (
                  <li key={item.id}>
                    <Link
                      to={destino(grupo, item)}
                      onClick={() => alternar(false)}
                      className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted focus-visible:bg-muted focus-visible:outline-none"
                    >
                      <Icone className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                      <span className="min-w-0 flex-1 truncate">{item.titulo}</span>
                      {grupo !== 'projetos' && <ChipProjeto projeto={item.projeto} />}
                      {item.arquivado && <Badge variant="secondary">Arquivado</Badge>}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ),
        )}
      </div>
    )
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        className="text-muted-foreground"
        aria-label="Buscar"
        onClick={() => setAberta(true)}
      >
        <Search /> <span className="hidden md:inline">Buscar</span>
        <kbd className="ml-2 hidden rounded border bg-muted px-1 text-[10px] lg:inline">Ctrl K</kbd>
      </Button>
      <Dialog open={aberta} onOpenChange={alternar}>
        <DialogContent aria-describedby={undefined} className="grid gap-3 sm:max-w-xl">
          <DialogTitle className="sr-only">Buscar</DialogTitle>
          <div className="relative pr-6">
            <Search
              className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              type="search"
              autoFocus
              aria-label="Buscar"
              placeholder="Projetos, tarefas, lembretes, anotações e documentos"
              className="pl-8"
              value={termo}
              onChange={(evento) => setTermo(evento.target.value)}
            />
          </div>
          {conteudo}
        </DialogContent>
      </Dialog>
    </>
  )
}

function Aviso({ children }: { children: ReactNode }) {
  return <p className="px-2 py-4 text-center text-sm text-muted-foreground">{children}</p>
}
