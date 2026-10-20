# 05 — Front-end

## 1. Stack

Use a versão estável mais recente de cada pacote no momento da instalação e registre no `package-lock.json`.

| Necessidade | Escolha |
| --- | --- |
| Base | React + TypeScript (`strict: true`, `noUncheckedIndexedAccess: true`) + Vite |
| Rotas | React Router (modo de rotas declarativas com `createBrowserRouter`) |
| Dados do servidor | TanStack Query |
| Cliente HTTP tipado | `openapi-fetch` + tipos gerados por `openapi-typescript` |
| Estilo | Tailwind CSS v4 (plugin `@tailwindcss/vite`) |
| Componentes | shadcn/ui (Radix) — copiados para `src/components/ui/` |
| Ícones | lucide-react |
| Toasts | sonner (via shadcn) |
| Formulários | react-hook-form + zod (`@hookform/resolvers`) |
| Arrastar e soltar | dnd-kit (`@dnd-kit/core`, `@dnd-kit/sortable`) |
| Testes | Vitest + Testing Library (+ jsdom); Playwright na Fase 7 |
| Qualidade | oxlint (config do template Vite + `react/exhaustive-deps`) e Prettier |

Não adicionar outras bibliotecas sem aprovação (sem Redux, Zustand, axios, moment, date-fns, styled-components).

## 2. Estrutura

```text
frontend/
  index.html
  vite.config.ts            # proxy /api -> http://127.0.0.1:8000; build.outDir = ../backend/app/static
  openapi.json              # exportado do back-end (gerado, versionado)
  src/
    main.tsx
    app/
      router.tsx            # rotas de 01-produto §3
      providers.tsx         # QueryClient, Toaster
      layout/               # Cabecalho, AbasPrincipais, MenuGeral, SinoAvisos
    api/
      schema.d.ts           # GERADO por `npm run gen:api` — não editar, não ler inteiro
      client.ts             # createClient<paths>({ baseUrl: "" }) + tratamento de erro
      chaves.ts             # query keys centralizadas
      erros.ts              # ErroApi + extração de mensagem/campos
    features/
      projetos/  tarefas/  lembretes/  documentos/  anotacoes/
      avisos/  hoje/  lixeira/  configuracoes/  busca/
        # cada uma: components/, hooks/ (useQuery/useMutation), e tipos locais se necessário
    components/
      ui/                   # shadcn
      comum/                # EditorRecorrencia, SeletorCor, ChipProjeto, TextoPrazo, EstadoVazio, ConfirmarDescartar
    lib/
      datas.ts              # formatação de datas (§6)
      cores.ts              # mapeamento cor → classes
      utils.ts              # cn() do shadcn
    test/setup.ts
```

## 3. Contrato com a API

- `npm run gen:api` executa `openapi-typescript openapi.json -o src/api/schema.d.ts --default-non-nullable false` (campos com valor padrão na API ficam opcionais nos tipos de entrada).
- O `openapi.json` é exportado pelo back-end com `uv run --directory backend python -m app.scripts.exportar_openapi ../frontend/openapi.json` (o caminho é relativo a `backend/`). A saída deve ser determinística: `json.dumps(app.openapi(), indent=2, ensure_ascii=False)` + quebra de linha final, sem depender de banco ou de data.
- Toda chamada passa pelo `client` tipado. Proibido `fetch` direto (exceto download de arquivo e upload com progresso, que usam `XMLHttpRequest` em `features/documentos/upload.ts`).
- Os tipos do front vêm de `components["schemas"][...]`. Não redefinir tipos que existem no schema.
- O CI falha se `openapi.json` ou `schema.d.ts` estiverem desatualizados.

## 4. Estado e dados

- Estado do servidor: **somente TanStack Query**. Estado de UI: `useState` local ou parâmetros de URL (ex.: `?tarefa=` abre o modal).
- Query keys em `api/chaves.ts`, por exemplo: `projetos.lista(arquivados)`, `projetos.detalhe(id)`, `tarefas.quadro(projetoId)`, `tarefas.detalhe(id)`, `tarefas.hoje()`, `lembretes.lista(projetoId)`, `avisos()`, `documentos.lista(projetoId)`, `anotacoes.lista(projetoId)`, `lixeira()`, `configuracoes()`.
- Cada mutação invalida exatamente as chaves afetadas. Tabela mínima:

  | Mutação | Invalida |
  | --- | --- |
  | tarefa (criar, editar, mover, concluir, desfazer, excluir) | `tarefas.quadro(p)`, `tarefas.hoje()`, `avisos()`, `projetos.lista(*)`, `tarefas.detalhe(id)` |
  | lembrete (qualquer) | `lembretes.lista(p)`, `avisos()`, `projetos.lista(*)` |
  | projeto (qualquer) | `projetos.*`, `avisos()`, `tarefas.hoje()` |
  | documento / anotação | a lista do projeto |
  | restaurar / excluir da lixeira | `lixeira()` e tudo do tipo restaurado |

- Atualização otimista **apenas** no arrastar e soltar (tarefas e projetos), com rollback e toast em caso de erro.
- `QueryClient`: `staleTime` 30 s, `refetchOnWindowFocus: true`, `retry: 1` para queries (exceto erro 4xx da API, que não muda ao repetir) e 0 para mutações.

## 5. Visual

- Fonte do sistema (pilha padrão do Tailwind). Fundo da página cinza (`neutral-200` a 70%); cards e áreas brancos com borda (`border`, mais escura que o padrão do shadcn) e sombra suave (`shadow-sm`; itens de lista `shadow-xs`), cantos `rounded-xl`, nunca sombras fortes. Texto secundário (`muted-foreground`) também mais escuro que o padrão, para a tela não ficar apagada. Cada área tem borda na cor dela e o cabeçalho separado do conteúdo por uma borda na mesma cor; as colunas do quadro são cinza com borda, com os cards brancos por cima.
- Todo elemento clicável mostra o cursor de mão (regra global em `index.css`, já que o Tailwind v4 não faz isso em botões); cards arrastáveis mostram o de arrastar. Itens clicáveis destacam a borda ou a sombra ao passar o mouse.
- **Cores das áreas** (definidas como variáveis CSS em `index.css`, usadas no cabeçalho de cada área como fundo `-100` + texto/ícone `-800`, e na borda da área `-300`):

  | Área | Cor | Ícone (lucide) |
  | --- | --- | --- |
  | Lembretes | âmbar (`amber`) | `Bell` |
  | Tarefas | azul (`blue`) | `SquareCheck` |
  | Documentos | verde (`emerald`) | `Folder` |
  | Anotações | roxo (`violet`) | `StickyNote` |

- Cores de projeto (RN-11) mapeadas em `lib/cores.ts` para uma classe de faixa/ponto: azul `blue-500`, verde `emerald-500`, roxo `violet-500`, laranja `orange-500`, rosa `pink-500`, vermelho `red-500`, ciano `cyan-500`, cinza `slate-400`.
- Cores de anotação: fundo `-100` e borda `-300` de amber, blue, emerald, pink, violet, slate.
- Prazo: vencido = `text-red-600`; hoje/amanhã = `text-amber-600`; demais = `text-muted-foreground`.
- Prioridade alta: ícone `ArrowUp` vermelho; baixa: `ArrowDown` cinza; média: sem ícone.
- Tema claro apenas.

## 6. Datas no front

- A API envia datas como `"AAAA-MM-DD"`. **Proibido** `new Date("2026-10-16")`: o JavaScript interpreta como UTC e, no Brasil, mostra o dia anterior.
- `lib/datas.ts` trabalha com strings: `formatarData("2026-10-16") → "16/10/2026"`, `formatarDataCurta(iso, anoAtual) → "16/10"`, `paraIso(dia, mes, ano)`.
- Textos relativos usam `dias_restantes` da API (RN-03). O front não calcula diferença de datas.
- Seletor de data: o componente de calendário do shadcn, convertendo a data selecionada para string com `paraIso` (usando getters locais `getFullYear/getMonth/getDate`, nunca `toISOString()`).
- Carimbos de tempo (`criado_em` etc.) podem usar `new Date(iso)` normalmente, pois têm `Z`.

## 7. Layout responsivo

- Alvo principal: computador. Não pode quebrar em telas menores.
- Projeto aberto:
  - ≥ 1280 px: três colunas — Lembretes 280 px | Tarefas flexível | Documentos + Anotações 300 px.
  - 768–1279 px: Tarefas em largura total; abaixo, Lembretes e Documentos/Anotações lado a lado.
  - < 768 px: tudo empilhado (Tarefas, Lembretes, Documentos, Anotações); colunas do quadro com rolagem horizontal.
- Home: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`.

## 8. Componentes-chave

- `PainelAvisos`: busca `avisos()` ao montar o layout; estado `fechado` em memória (zera ao recarregar, RN-52/53). Escuta `visibilitychange`/`focus`: se `GET /api/saude` devolver um `hoje` diferente do último visto, refaz `avisos()` e reabre.
- `QuadroTarefas`: dnd-kit com `SortableContext` por coluna; ao soltar, chama `mover` com `status` e `indice`. Cards de meta mensal com `disabled` para troca de coluna. Animação: o card levantado acompanha o cursor (leve inclinação e sombra), o lugar de destino fica tracejado e, ao soltar, a arrumação nova permanece até o cache trazer o quadro previsto (o card nunca volta à coluna antiga antes de assentar).
- `EditorRecorrencia`: controla o objeto `Recorrencia` (RN-30) e mostra a frase usando o mesmo texto de RN-35 (pré-visualização local; o texto oficial vem da API depois de salvar).
- `ModalTarefa`, `ModalProjeto`, `ModalLembrete`, `ModalAnotacao`: react-hook-form + zod; schema zod espelha as validações da API; erros 422 da API são aplicados aos campos com `setError`.
- `ConfirmarDescartar`: diálogo padrão para fechar modal com alterações (RN-85).

## 9. Acessibilidade e UX

- Todo botão só com ícone tem `aria-label`. Foco visível em todos os controles.
- Modais e menus do Radix (gerenciam foco e `Esc`).
- Arrastar e soltar também funciona por teclado (sensor de teclado do dnd-kit).
- Ações destrutivas definitivas (excluir da lixeira, esvaziar) pedem confirmação; exclusão comum não pede, pois vai para a lixeira e tem **Desfazer** no toast.
- Carregamento: skeletons nas listas; botões de ação mostram estado de carregando e ficam inativos durante a requisição.
- Textos longos: `line-clamp` nos cards, texto completo no modal. Descrições com `whitespace-pre-wrap`.
