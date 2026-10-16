# 08 — Roadmap

Regras:

- Execute as tarefas **na ordem**. Uma tarefa por sessão do Claude Code (use `/proxima-tarefa`).
- Cada tarefa lista os documentos a ler. Leia só eles.
- Marque `[x]` apenas quando os critérios de aceite forem cumpridos e a skill `verify` passar.
- Ao concluir uma tarefa, faça um commit: `feat(fase-1.4): modelo e API de tarefas simples` (tipos: feat, fix, test, refactor, docs, chore).

## Fase 0 — Fundação

- [x] **0.1 Esqueleto do back-end** · ler: 06 §2–4, §6, §7
  `pyproject.toml` (uv, deps de 06 §2, ruff, mypy strict, pytest com cobertura), estrutura de pastas de 06 §3 (pastas vazias com `__init__.py`), `config.py`, `clock.py` (+ `ClockFixo` para testes), `db/base.py` com naming convention, `db/tipos.py` (`UTCDateTime`), `db/sessao.py` com PRAGMAs, `erros.py` com o formato de erro de 04, `main.py` com `GET /api/saude`.
  Aceite: teste de `/api/saude` com relógio fixo; teste de erro 404 e 422 no formato padrão; teste dos PRAGMAs ativos; ruff e mypy limpos.

- [x] **0.2 Migrations e inicialização** · ler: 06 §5, §9; 02 RN-112
  Alembic com `render_as_batch`, migration inicial (tabela `configuracoes`), `db/migracoes.py`, lifespan (passos 1–4 de 06 §9), configurações padrão (RN-100).
  Aceite: teste de inicialização com pasta vazia; teste de backup pré-migração; teste `upgrade head` + comparação sem diferenças.

- [x] **0.3 Esqueleto do front-end** · ler: 05 §1, §2, §5, §7
  Vite + React + TS strict, Tailwind v4, shadcn (init + `button dialog input textarea select dropdown-menu badge checkbox tooltip sonner tabs popover calendar label switch alert-dialog skeleton`), React Router com as rotas de 01 §3 (telas vazias), TanStack Query, layout com cabeçalho e abas, proxy `/api`, scripts `dev build lint typecheck test gen:api`, Vitest configurado.
  A pasta `frontend/` já contém `CLAUDE.md`: gere o template do Vite numa pasta temporária e mova os arquivos para `frontend/` sem apagar o `CLAUDE.md` (o mesmo vale para `backend/` na 0.1).
  Aceite: `build`, `lint`, `typecheck`, `test` passam; o cabeçalho mostra a versão vinda de `/api/saude`.

- [x] **0.4 Contrato tipado** · ler: 04 Convenções; 05 §3
  `app/scripts/exportar_openapi.py`, `operation_id` explícito, `npm run gen:api`, `api/client.ts`, `api/erros.ts`, `api/chaves.ts`; faixa "Data simulada" no cabeçalho (06 §6) com `formatarData` em `lib/datas.ts`.
  Aceite: o front consome `/api/saude` pelo client tipado; o passo "Contrato" do CI passa localmente.

- [x] **0.5 Modo de uso local** · ler: 06 §10, §11
  Build do Vite em `backend/app/static`, `StaticFiles` + fallback da SPA, `cli.py` (`frentes`, `frentes iniciar`) com abertura do navegador e mensagem de porta ocupada; padrões do `QueryClient` (05 §4).
  Aceite: teste do fallback da SPA e do 404 em `/api/inexistente`; execução manual de `frentes` abre o app.

- [x] **0.6 CI e README de execução** · ler: 07 §6
  Conferir `.github/workflows/ci.yml` com os comandos reais; README com como rodar.
  Aceite: CI verde no GitHub.

## Fase 1 — Projetos e tarefas simples

- [x] **1.1 Projetos: modelo e API** · ler: 03 (projetos, convenções); 04 Projetos; 02 RN-10..17, RN-90
  Modelo, migration, schemas, repository, service, router; `busca` preenchida; exclusão lógica; reordenar.
  Aceite: testes de 07 §3.5 (RN-12 parcial, RN-15, RN-16) e CRUD.

- [x] **1.2 Home de projetos** · ler: 01 §4.2, §4.6 (Projeto); 05 §4, §5
  Grade de cards, modal de projeto (criar/editar), menu do card, reordenar arrastando (otimista), estado vazio, excluir com Desfazer.
  Aceite: testes de componente do modal; verificação manual dos fluxos.

- [x] **1.3 Arquivados** · ler: 01 §4.7; 02 RN-12
  Tela Arquivados, reabrir.
  Aceite: teste de API do filtro `arquivados`; fluxo manual.

- [x] **1.4 Tarefas simples: modelo e API** · ler: 03 (tarefas, tarefa_execucoes); 04 Tarefas; 02 RN-20..22, RN-25..27
  Modelo com CHECK `tipo_campos` (os três tipos já no modelo), migration, `GET quadro`, criar, editar, excluir, mover com renumeração, concluir/desfazer (simples).
  Aceite: testes de 07 §3.3 para simples (RN-21 inclusive).

- [x] **1.5 Página do projeto e quadro** · ler: 01 §4.4; 05 §7, §8
  Cabeçalho do projeto, layout de 3 colunas (Lembretes, Documentos e Anotações com estado "em breve"), quadro com dnd-kit (mouse e teclado), criação rápida.
  Aceite: arrastar entre colunas e reordenar persiste após recarregar; layout correto nas 3 larguras.

- [x] **1.6 Modal da tarefa** · ler: 01 §4.5; 02 RN-85
  Abrir por `?tarefa=`, editar, concluir, excluir, Desfazer no toast, confirmação ao descartar.
  Aceite: testes de componente; fluxo manual.

- [x] **1.7 Progresso opcional** · ler: 02 RN-13
  Cálculo no resumo do projeto; barra no card e no cabeçalho só quando ligado.
  Aceite: testes de RN-13.

> **Marco 1:** já dá para usar no dia a dia para projetos e tarefas.

## Fase 2 — Recorrência e metas

- [ ] **2.1 Domínio de recorrência** · ler: 02 RN-30..36; 07 §3.1
  `domain/recorrencia.py`: modelo Pydantic `Recorrencia` com validação, `proxima_ocorrencia`, `avancar`, `ocorrencias_atrasadas`, `descrever`.
  Aceite: **todos** os casos de 07 §3.1; cobertura ≥ 95% no módulo.

- [ ] **2.2 Tarefa repetida** · ler: 02 RN-21, RN-23, RN-26
  Criar/editar com recorrência, concluir avança, mover para Concluída = concluir, desfazer, `recorrencia_descricao`, histórico no detalhe.
  Aceite: testes de 07 §3.3 (repetida).

- [ ] **2.3 Meta mensal** · ler: 02 RN-24, RN-26
  +1, −1, `progresso_mes`, status derivado, bloqueio de troca de coluna, execuções do mês no detalhe.
  Aceite: testes de 07 §3.3 (meta), incluindo virada de mês.

- [ ] **2.4 Interface de recorrência e metas** · ler: 01 §4.4 (Tarefas), §4.5, §4.6 (editor); 05 §8
  `EditorRecorrencia` (reutilizável), campos por tipo no modal, selos "repete"/"meta 2/4", botões +1/−1.
  Aceite: testes unitários do editor (07 §4).

## Fase 3 — Lembretes, avisos e Tarefas de hoje

- [ ] **3.1 Lembretes: modelo e API** · ler: 03 (lembretes, lembrete_baixas); 04 Lembretes; 02 RN-40..46
  Aceite: testes de 07 §3.4.

- [ ] **3.2 Área de lembretes no projeto** · ler: 01 §4.4 (Lembretes), §4.6 (Lembrete)
  Lista, destaque de janela/vencido, modal, dar baixa com Desfazer, seção Concluídos com Reativar.
  Aceite: fluxo manual; teste de componente do item.

- [ ] **3.3 Domínio e API de avisos** · ler: 02 RN-50..58; 07 §3.2
  `domain/avisos.py` + `GET /api/avisos` + contador `avisos` no resumo do projeto (RN-57).
  Aceite: todos os casos de 07 §3.2.

- [ ] **3.4 Painel de avisos e sino** · ler: 01 §3, §4.1; 05 §8 (PainelAvisos)
  Aceite: testes de componente de 07 §4; teste manual da reabertura ao mudar o dia usando `FRENTES_HOJE_SIMULADO` (06 §6).

- [ ] **3.5 Tarefas de hoje** · ler: 01 §4.3; 02 RN-60..63; 04 `GET /tarefas/hoje`
  API + tela + contador da aba.
  Aceite: testes de 07 §3.5 (RN-60..62) e de componente da linha de atrasadas.

> **Marco 2:** uso diário completo (projetos, tarefas, recorrências, lembretes e avisos).

## Fase 4 — Documentos e anotações

- [ ] **4.1 Storage e API de documentos** · ler: 06 §8, §12; 03 (documentos); 04 Documentos; 02 RN-70..73
  Aceite: todos os casos de 07 §3.7.

- [ ] **4.2 Área de documentos** · ler: 01 §4.4 (Documentos)
  Soltar arquivos, progresso por arquivo (`XMLHttpRequest`), lista, abrir/baixar, renomear, excluir.
  Aceite: fluxo manual com PDF, imagem e .xlsx.

- [ ] **4.3 Anotações** · ler: 03 (anotacoes); 04 Anotações; 02 RN-80..81; 01 §4.4, §4.6
  Modelo, API, área com cards coloridos, modal, fixar.
  Aceite: testes de API (ordem RN-81) e fluxo manual.

## Fase 5 — Proteções

- [ ] **5.1 Lixeira** · ler: 02 RN-90..94; 04 Lixeira; 01 §4.8
  API, purga na inicialização (passo 5 de 06 §9), tela.
  Aceite: todos os casos de 07 §3.6.

- [ ] **5.2 Configurações** · ler: 02 RN-100; 04 Configurações; 01 §4.9
  Aceite: teste de API; alterar `aviso_tarefas_dias` muda os avisos.

- [ ] **5.3 Backup e restauração** · ler: 02 RN-110..112; 06 §11
  `GET /api/backup`, botão em Configurações e no menu, `frentes backup`, `frentes restaurar`.
  Aceite: casos de backup/restauração de 07 §3.8.

## Fase 6 — Polimento

- [ ] **6.1 Busca global** · ler: 02 RN-120..121; 04 Busca
  `domain/textos.normalizar_busca`, endpoint, caixa de busca com `Ctrl+K`.
  Aceite: busca ignora acentos e maiúsculas; não retorna excluídos.

- [ ] **6.2 Atalhos e estados** · ler: 02 RN-130; 05 §9
  Atalhos, estados vazios de todas as telas, skeletons, mensagens de erro.

- [ ] **6.3 Revisão de responsividade e acessibilidade** · ler: 05 §7, §9
  Navegação completa por teclado; layouts nas 3 larguras.

## Fase 7 — Distribuição e portfólio

- [ ] **7.1 Testes ponta a ponta** · ler: 07 §5
  Playwright com os 6 fluxos; script `npm --prefix frontend run e2e`.

- [ ] **7.2 README de portfólio**
  GIF de 20–30 s, funcionalidades, decisões técnicas (resumo de 09), arquitetura, como rodar, testes.

- [ ] **7.3 Executável (opcional)** · ler: 06 §11
  PyInstaller `onedir`; instruções no README.

> **Marco 3:** projeto publicado no GitHub e no LinkedIn.
