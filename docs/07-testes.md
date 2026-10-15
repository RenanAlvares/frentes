# 07 — Testes e qualidade

## 1. Princípios

- Toda regra (RN-xx) implementada tem teste que cita o código.
- Lógica com datas é testada com **relógio fixo**, nunca com a data real.
- Tarefa só está pronta quando a skill `verify` passa (lint, tipos, testes e build dos dois lados).
- Teste de bug: primeiro um teste que falha reproduzindo o bug, depois a correção.

## 2. Back-end

- `pytest` com `pytest-cov`. Configuração em `pyproject.toml`: `addopts = "-q --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=85"`, `testpaths = ["tests"]`.
- `tests/unit/`: funções puras (`domain/`), sem banco.
- `tests/api/`: rotas via `TestClient`, cada teste com banco novo.
- Fixtures em `conftest.py`:
  - `pasta_dados` (`tmp_path`): `FRENTES_DATA_DIR` temporário.
  - `app` e `client`: `create_app()` com `Settings` de teste e `ClockFixo(date(2026, 10, 14))` (uma quarta-feira).
  - `relogio`: permite trocar a data dentro do teste (`relogio.definir(date(2026, 10, 31))`).
  - Fábricas simples (`criar_projeto(client, **campos)`, `criar_tarefa(...)`, `criar_lembrete(...)`) que usam a própria API.
- Banco de teste: SQLite em arquivo dentro de `tmp_path` (exercita os PRAGMAs e as migrations reais).
- Meta de cobertura: **≥ 95% em `app/domain/`**, ≥ 90% em `app/services/`, ≥ 85% no total (o CI falha abaixo disso).

## 3. Casos obrigatórios

### 3.1 Recorrência (`tests/unit/test_recorrencia.py`, parametrizado)

`avancar(regra, atual, hoje)` — datas de 2026, onde 12/10 é segunda e 14/10 é quarta:

| # | Regra | atual | hoje | Esperado | RN |
| --- | --- | --- | --- | --- | --- |
| 1 | diária, 1 | 2026-10-14 | 2026-10-14 | 2026-10-15 | 31/32 |
| 2 | diária, 7 | 2026-10-01 | 2026-10-14 | 2026-10-15 | 32 |
| 3 | diária, 7 | 2026-10-20 | 2026-10-14 | 2026-10-27 | 32 (ainda não venceu) |
| 4 | semanal, 1, [seg] | 2026-10-12 | 2026-10-14 | 2026-10-19 | 31 |
| 5 | semanal, 1, [seg, qua] | 2026-10-12 | 2026-10-12 | 2026-10-14 | 31 |
| 6 | semanal, 2, [seg] | 2026-10-12 | 2026-10-12 | 2026-10-26 | 31 |
| 7 | semanal, 1, [seg] | 2026-10-14 (quarta) | 2026-10-14 | 2026-10-19 | 33 |
| 8 | mensal, 1, dia 31 | 2026-01-31 | 2026-01-31 | 2026-02-28 | 31 |
| 9 | mensal, 1, dia 31 | 2026-02-28 | 2026-02-28 | 2026-03-31 | 31 (não "gruda" no 28) |
| 10 | mensal, 1, dia 30 | 2028-01-30 | 2028-01-30 | 2028-02-29 | 31 (bissexto) |
| 11 | mensal, 3, dia 10 | 2026-10-10 | 2026-10-14 | 2027-01-10 | 31 |
| 12 | mensal, 1, dia 5 | 2026-10-03 | 2026-10-03 | 2026-10-05 | 33 |
| 13 | mensal, 1, dia 5 | 2026-08-05 | 2026-10-14 | 2026-11-05 | 32 (pula perdidas) |
| 14 | anual, 1, 29/02 | 2028-02-29 | 2028-02-29 | 2029-02-28 | 31 |
| 15 | anual, 1, 29/02 | 2031-02-28 | 2031-02-28 | 2032-02-29 | 31 |
| 16 | diária, 1 | 2026-10-10 | 2026-10-14 | 2026-10-15 | 32 |
| 17 | anual, 2, 20/11 | 2026-11-20 | 2026-11-20 | 2028-11-20 | 31 |

`ocorrencias_atrasadas(regra, atual, hoje)`:

| Regra | atual | hoje | Esperado |
| --- | --- | --- | --- |
| mensal, 1, dia 5 | 2026-08-05 | 2026-10-14 | 3 |
| diária, 1 | 2026-10-10 | 2026-10-14 | 5 |
| qualquer | 2026-10-20 | 2026-10-14 | 0 |
| qualquer | 2026-10-14 | 2026-10-14 | 1 |
| diária, 1 | 2026-01-01 | 2026-10-14 | 99 (limite) |

`descrever(regra)`: todos os exemplos da tabela de RN-35.

Validação da regra (RN-30): semanal sem dias → erro; `dias_semana` fora de 0–6 → erro; mensal sem `dia_mes` → erro; anual sem `mes` → erro; `intervalo` 0 ou 366 → erro; campo que não se aplica preenchido → erro.

### 3.2 Avisos (`tests/unit/test_avisos.py` e `tests/api/test_avisos.py`), hoje = 2026-10-14

- Lembrete vencimento 17/10, antecedência 3 → aparece, `dias_restantes = 3` (primeiro dia da janela, RN-42).
- Vencimento 18/10, antecedência 3 → não aparece.
- Antecedência 0, vencimento hoje → aparece com 0.
- Vencimento 11/10 → aparece com −3; recorrente mensal com vencimento 05/08 → `ocorrencias_atrasadas = 3`.
- Lembrete concluído, excluído, de projeto concluído ou de projeto excluído → não aparece (RN-41/50).
- Tarefa simples com prazo 17/10 → aparece (aviso_tarefas_dias = 3); concluída → não; sem prazo → não.
- Alterar `aviso_tarefas_dias` para 0 → a tarefa de 17/10 some.
- Meta 2/4: em 14/10 não aparece; com relógio em 29/10 aparece com `dias_restantes = 2` e `meta = {feitas: 2, meta: 4}`; com 4/4 não aparece.
- Ordenação RN-51: vencido −3, lembrete 0, tarefa 0, tarefa 2 — nessa ordem; empate de tipo resolvido pelo título.

### 3.3 Tarefas

- RN-22: concluir simples grava `concluida_em`; mover de volta limpa.
- RN-23: concluir repetida registra execução com `prazo_referencia`, avança o prazo e mantém `pendente`; mover repetida para Concluída tem o mesmo efeito.
- RN-24: +1 três vezes em outubro → `progresso_mes = 3`; relógio em 01/11 → 0; −1 sem execuções no mês → 409; mover meta para outra coluna → 409; status derivado `concluida` quando atinge a meta.
- RN-25: mover para o índice 0, para o meio e além do fim; posições renumeradas 0..n−1 nas duas colunas; Concluída ordenada por `concluida_em` e limitada a 20 com `total_concluidas` correto.
- RN-26: desfazer em cada tipo; desfazer sem histórico → 409.
- RN-21: combinações inválidas de tipo e campos → 422 com `campos`; CHECK do banco também rejeita (teste direto no modelo).
- RN-13: progresso conta só simples não excluídas.

### 3.4 Lembretes

- RN-43 não recorrente: baixa grava `concluido_em`; aparece em `concluidos`.
- RN-43 recorrente: baixa registra ocorrência e avança; baixa antes da janela também avança.
- RN-44: desfazer restaura exatamente o estado anterior, nos dois casos.

### 3.5 Projetos e Tarefas de hoje

- RN-12: projeto concluído some de `GET /projetos`, aparece com `arquivados=true`, e suas tarefas somem de `/tarefas/hoje` e `/avisos`.
- RN-15: `PUT /projetos/ordem` grava as posições; ids faltando ou sobrando → 422.
- RN-16: `data_inicio > prazo` → 422.
- RN-60/61/62: hoje x atrasadas x futuras; ordenação por prioridade; metas no último dia do mês.

### 3.6 Lixeira

- RN-90: excluídos somem das listas, do progresso, dos avisos.
- RN-91: projeto excluído aparece sozinho na lixeira (sem seus itens); item excluído individualmente de projeto ativo aparece.
- RN-92: restaurar projeto traz os itens; item excluído antes continua na lixeira.
- RN-93: excluir definitivo apaga linhas dependentes e arquivos físicos.
- RN-94: com relógio 31 dias depois, a inicialização purga; com 29 dias, não.

### 3.7 Documentos

- Upload de 2 arquivos → 2 registros e 2 arquivos no disco com nomes `uuid.ext`.
- Arquivo acima do limite → 413, nenhum registro, nenhum arquivo parcial.
- Nome `../../etc/passwd` e `con.txt` → salvos com chave segura; nome exibido preservado.
- Download de PDF → `inline`; de HTML/SVG → `attachment`; sempre `nosniff`; nome com acento no `filename*`.
- Renomear mantém a extensão; nome com `/` → 422.

### 3.8 Infraestrutura

- `alembic upgrade head` em banco vazio + comparação de metadados sem diferenças.
- Inicialização com pasta vazia cria `frentes.db`, `anexos/`, `backups/` e as configurações padrão.
- Backup pré-migração criado só quando há migration pendente; mantém 5.
- `GET /api/backup` → zip com `frentes.db`, `anexos/` e `manifest.json` válido; o `frentes.db` do zip abre e tem os dados.
- `frentes restaurar` com zip válido substitui os dados e guarda os antigos; zip com revisão mais nova → recusa.
- Erros: rota inexistente em `/api` → 404 no formato padrão; validação → 422 com `campos` em português.
- SPA: `GET /projetos/123` devolve `index.html` (quando o build existe).
- Nenhum uso de `date.today()`, `datetime.utcnow()` ou `datetime.now(` em `app/`, exceto em `app/clock.py` (teste que procura no código-fonte).

## 4. Front-end

- Vitest + Testing Library, ambiente jsdom.
- Unitários obrigatórios: `lib/datas.ts` (formatação, `paraIso`, nunca deslocar dia), mapeamento do `EditorRecorrencia` para o JSON de RN-30, pré-visualização de RN-35.
- Componentes: `PainelAvisos` (3 itens + "Ver mais N", fechar, sem avisos não renderiza), linha "N atrasadas" (oculta com 0, expande ao clicar), `ModalTarefa` (campos por tipo, confirmação ao descartar).
- Chamadas de rede simuladas no nível do `client` (não testar a biblioteca).

## 5. Ponta a ponta (Fase 7, Playwright)

Rodam contra o app em modo de uso, com pasta de dados temporária:

1. Criar projeto, criar tarefa rápida, arrastar para Em andamento e depois Concluída; progresso atualiza.
2. Criar lembrete vencendo em 2 dias → recarregar → painel de avisos mostra; dar baixa → some; desfazer → volta.
3. Tarefa repetida semanal: concluir → prazo avança uma semana.
4. Meta mensal 2x: +1, +1 → vai para Concluída.
5. Upload de PDF, abrir, renomear, excluir, restaurar da lixeira.
6. Concluir projeto → some da home → reabrir em Arquivados.

## 6. Ferramentas de qualidade

| Lado | Comando | Regra |
| --- | --- | --- |
| Back | `uv run --directory backend ruff check .` | regras `E, F, I, B, UP, SIM, RUF`; linha 100 |
| Back | `uv run --directory backend ruff format --check .` | |
| Back | `uv run --directory backend mypy app` | `strict = true` (com plugin pydantic) |
| Back | `uv run --directory backend pytest` | cobertura conforme §2 |
| Front | `npm --prefix frontend run lint` | oxlint sem avisos (`--deny-warnings`) |
| Front | `npm --prefix frontend run typecheck` | `tsc -b --noEmit` |
| Front | `npm --prefix frontend run test` | `vitest run` |
| Front | `npm --prefix frontend run build` | |
| Contrato | exportar openapi + `gen:api` + `git diff --exit-code` | nada a mudar |
