# 04 — API

## Convenções

- Prefixo `/api`. JSON em `snake_case`. Sem paginação (volumes de um usuário), exceto onde indicado.
- Datas: `"AAAA-MM-DD"`. Carimbos de tempo: ISO 8601 em UTC com `Z` (`"2026-10-14T22:30:00Z"`).
- IDs: UUID em string.
- Criar → `201` com o recurso. Atualizar → `200` com o recurso. Excluir → `204`.
- `PATCH` aceita só os campos enviados; campos ausentes não mudam.
- Respostas e entradas definidas por modelos Pydantic em `app/schemas/`. O OpenAPI gerado é o contrato: o front usa tipos gerados dele (`05-frontend.md` §3).
- Toda rota tem `operation_id` explícito em `snake_case` (ex.: `listar_projetos`) para gerar nomes estáveis.

## Formato de erro

Todos os erros, inclusive de validação, saem neste formato:

```json
{"erro": {"codigo": "validacao", "mensagem": "Revise os campos destacados.", "campos": {"nome": "Informe o nome do projeto."}}}
```

| HTTP | `codigo` | Quando |
| --- | --- | --- |
| 404 | `nao_encontrado` | Recurso inexistente ou na lixeira |
| 409 | `conflito` | Ação inválida para o estado atual (ex.: mover meta entre colunas, desfazer sem histórico) |
| 413 | `arquivo_grande` | Upload acima do limite |
| 422 | `validacao` | Entrada inválida; `campos` mapeia campo → mensagem em português |
| 500 | `erro_interno` | Erro não tratado (mensagem genérica; detalhes só no log) |
| outro (ex.: 405) | `requisicao_invalida` | Erro HTTP fora desta tabela; mantém o status original |

`campos` só aparece nos erros de validação.

## Modelos de resposta

```text
Progresso      { concluidas: int, total: int }
ProjetoResumo  { id, nome, status, cor, prazo, acompanhar_progresso, progresso: Progresso|null, avisos: int, posicao }
Projeto        ProjetoResumo + { descricao, data_inicio, criado_em, atualizado_em }
Recorrencia    { frequencia, intervalo, dias_semana: int[]|null, dia_mes: int|null, mes: int|null }
Tarefa         { id, projeto_id, titulo, descricao, status, prioridade, tipo, prazo, recorrencia: Recorrencia|null,
                 recorrencia_descricao: str|null, meta_mensal: int|null, progresso_mes: int|null,
                 posicao, concluida_em, atrasada: bool, criado_em, atualizado_em }
TarefaDetalhe  Tarefa + { execucoes: [{ data, criado_em }] }   # repetida: últimas 5; meta: as do mês
Quadro         { pendente: Tarefa[], em_andamento: Tarefa[], concluida: Tarefa[], total_concluidas: int }
TarefaHoje     Tarefa + { projeto: { id, nome, cor } }
Lembrete       { id, projeto_id, titulo, observacao, vencimento, antecedencia_dias, recorrencia, recorrencia_descricao,
                 dias_restantes: int, na_janela: bool, ocorrencias_atrasadas: int, concluido_em, criado_em, atualizado_em }
Documento      { id, projeto_id, nome, extensao, mime, tamanho_bytes, abre_no_navegador: bool, criado_em }
Anotacao       { id, projeto_id, titulo, texto, cor, fixada, criado_em, atualizado_em }
Aviso          { tipo: "lembrete"|"tarefa", id, titulo, projeto: { id, nome, cor }, vencimento, dias_restantes,
                 ocorrencias_atrasadas: int, meta: { feitas, meta }|null }
ItemLixeira    { tipo: "projeto"|"tarefa"|"lembrete"|"documento"|"anotacao", id, titulo, projeto_nome: str|null,
                 excluido_em, expira_em }
Configuracoes  { aviso_tarefas_dias: int, antecedencia_padrao_lembretes: int }
```

## Endpoints

### Sistema

| Método e rota | Descrição |
| --- | --- |
| `GET /api/saude` | `{ status: "ok", versao, hoje, hoje_simulado: bool }` — `hoje` segundo RN-01 (o front usa para detectar a virada do dia, RN-53) |

### Projetos

| Método e rota | Entrada | Saída |
| --- | --- | --- |
| `GET /api/projetos?arquivados=false` | `arquivados=true` lista só concluídos | `ProjetoResumo[]` por `posicao` |
| `POST /api/projetos` | `nome`, `descricao?`, `status?`, `cor?`, `data_inicio?`, `prazo?`, `acompanhar_progresso?` | `Projeto` |
| `GET /api/projetos/{id}` | | `Projeto` |
| `PATCH /api/projetos/{id}` | mesmos campos, opcionais | `Projeto` |
| `DELETE /api/projetos/{id}` | | 204 (lixeira) |
| `PUT /api/projetos/ordem` | `{ ids: uuid[] }` — todos os projetos não arquivados | 204 |

### Tarefas

| Método e rota | Entrada | Saída |
| --- | --- | --- |
| `GET /api/projetos/{id}/tarefas` | | `Quadro` |
| `GET /api/projetos/{id}/tarefas/concluidas` | | `Tarefa[]` (todas as concluídas, "Ver todas") |
| `POST /api/projetos/{id}/tarefas` | `titulo`, `descricao?`, `prioridade?`, `tipo?`, `prazo?`, `recorrencia?`, `meta_mensal?` | `Tarefa` |
| `GET /api/tarefas/{id}` | | `TarefaDetalhe` |
| `PATCH /api/tarefas/{id}` | campos editáveis, opcionais (inclui `status`) | `Tarefa` |
| `DELETE /api/tarefas/{id}` | | 204 (lixeira) |
| `POST /api/tarefas/{id}/mover` | `{ status, indice }` (RN-25) | `Quadro` do projeto |
| `POST /api/tarefas/{id}/concluir` | | `Tarefa` (simples → concluída; repetida → avança; meta → +1) |
| `POST /api/tarefas/{id}/desfazer-conclusao` | | `Tarefa` (RN-26) |
| `POST /api/tarefas/{id}/execucoes/remover-ultima` | | `Tarefa` (meta "−1", RN-24) |
| `GET /api/tarefas/hoje` | | `{ atrasadas: TarefaHoje[], hoje: TarefaHoje[] }` |

`PATCH` com `status` em tarefa repetida para `concluida` equivale a `concluir`. `PATCH` com `status` em meta → 409.

### Lembretes

| Método e rota | Entrada | Saída |
| --- | --- | --- |
| `GET /api/projetos/{id}/lembretes` | | `{ ativos: Lembrete[], concluidos: Lembrete[] }` |
| `POST /api/projetos/{id}/lembretes` | `titulo`, `observacao?`, `vencimento`, `antecedencia_dias?`, `recorrencia?` | `Lembrete` |
| `PATCH /api/lembretes/{id}` | campos, opcionais (`recorrencia: null` remove a repetição) | `Lembrete` |
| `DELETE /api/lembretes/{id}` | | 204 |
| `POST /api/lembretes/{id}/baixa` | | `Lembrete` (RN-43) |
| `POST /api/lembretes/{id}/desfazer-baixa` | | `Lembrete` (RN-44) |

### Avisos

| Método e rota | Saída |
| --- | --- |
| `GET /api/avisos` | `{ total: int, itens: Aviso[] }` ordenado por RN-51 |

### Documentos

| Método e rota | Entrada | Saída |
| --- | --- | --- |
| `GET /api/projetos/{id}/documentos` | | `Documento[]` |
| `POST /api/projetos/{id}/documentos` | `multipart/form-data`, campo `arquivos` (um ou mais) | `Documento[]` criados |
| `GET /api/documentos/{id}/arquivo` | | o arquivo (RN-71: `Content-Disposition` inline ou attachment, `nosniff`, nome em `filename*=UTF-8''…`) |
| `PATCH /api/documentos/{id}` | `{ nome }` | `Documento` |
| `DELETE /api/documentos/{id}` | | 204 |

Upload: o limite vale **por arquivo**; se um passar do limite, nenhum arquivo daquela requisição é gravado (413).

### Anotações

| Método e rota | Entrada | Saída |
| --- | --- | --- |
| `GET /api/projetos/{id}/anotacoes` | | `Anotacao[]` (RN-81) |
| `POST /api/projetos/{id}/anotacoes` | `titulo?`, `texto`, `cor?`, `fixada?` | `Anotacao` |
| `PATCH /api/anotacoes/{id}` | campos, opcionais | `Anotacao` |
| `DELETE /api/anotacoes/{id}` | | 204 |

### Lixeira

| Método e rota | Saída |
| --- | --- |
| `GET /api/lixeira` | `ItemLixeira[]` por `excluido_em` decrescente |
| `POST /api/lixeira/{tipo}/{id}/restaurar` | 204 |
| `DELETE /api/lixeira/{tipo}/{id}` | 204 (definitivo) |
| `DELETE /api/lixeira` | 204 (esvaziar) |

### Configurações e backup

| Método e rota | Entrada | Saída |
| --- | --- | --- |
| `GET /api/configuracoes` | | `Configuracoes` |
| `PATCH /api/configuracoes` | campos, opcionais | `Configuracoes` |
| `GET /api/backup` | | arquivo `.zip` (RN-110) |

### Busca (Fase 6)

| Método e rota | Saída |
| --- | --- |
| `GET /api/busca?q=termo` | `{ projetos: [...], tarefas: [...], lembretes: [...], anotacoes: [...], documentos: [...] }`, cada item com `id`, `titulo`, `projeto: {id, nome, cor}`, `arquivado: bool` |

## SPA

Qualquer `GET` que não comece com `/api` nem `/assets` devolve `index.html` (roteamento do React). `/api/*` inexistente devolve 404 no formato de erro, nunca o `index.html`.
