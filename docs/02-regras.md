# 02 — Regras de negócio

Cada regra tem um código. Testes devem citar o código no nome ou docstring (ex.: `test_rn42_lembrete_aparece_no_primeiro_dia_da_janela`).

## Datas e tempo

- **RN-01** "Hoje" é a data atual no fuso `FRENTES_TIMEZONE` (padrão `America/Sao_Paulo`), calculada **somente no back-end** por `clock.hoje()`. O front nunca calcula "hoje" para regras.
- **RN-02** Prazos, vencimentos e datas de execução são **datas sem hora** (`date`). Carimbos de tempo (`criado_em`, `atualizado_em`, `excluido_em`, `concluido_em`, `concluida_em`) são `datetime` em **UTC**.
- **RN-03** `dias_restantes = (vencimento − hoje)` em dias. Texto relativo: `< 0` → "vencido há N dia(s)"; `0` → "vence hoje"; `1` → "vence amanhã"; `≥ 2` → "vence em N dias". O texto é montado no front a partir de `dias_restantes` vindo da API.

## Projetos

- **RN-10** Campos: `nome` (1–100 caracteres, obrigatório, espaços nas pontas removidos), `descricao` (até 2000), `status`, `cor`, `data_inicio` (opcional), `prazo` (opcional), `acompanhar_progresso` (padrão `false`).
- **RN-11** Status: `planejado`, `em_andamento`, `aguardando`, `concluido`. Novo projeto nasce `em_andamento`. Cores: `azul`, `verde`, `roxo`, `laranja`, `rosa`, `vermelho`, `ciano`, `cinza` (padrão `azul`).
- **RN-12** Projeto `concluido` está **arquivado**: sai da home, aparece em Arquivados, e suas tarefas e lembretes deixam de gerar avisos e de aparecer em Tarefas de hoje. "Reabrir" muda o status para `em_andamento`.
- **RN-13** Progresso (somente se `acompanhar_progresso = true`): `concluidas / total`, contando **apenas tarefas simples não excluídas**. Repetidas e metas não entram. Total 0 → barra vazia e texto "Sem tarefas".
- **RN-14** O prazo do projeto é informativo: não gera aviso.
- **RN-15** Ordem na home por `posicao` (crescente). Novo projeto vai para o fim. Reordenar envia a lista completa de ids e o back-end grava `posicao = índice`.
- **RN-16** Se `data_inicio` e `prazo` existirem, `data_inicio ≤ prazo` (senão erro de validação).
- **RN-17** Projeto **ativo** = não excluído e status diferente de `concluido`.

## Tarefas

- **RN-20** Campos: `titulo` (1–200, obrigatório), `descricao` (até 5000, texto puro; quebras de linha preservadas), `prioridade` (`baixa`, `media`, `alta`; padrão `media`), `status` (`pendente`, `em_andamento`, `concluida`; padrão `pendente`), `tipo`, `prazo`, `recorrencia`, `meta_mensal`.
- **RN-21** Tipos e campos obrigatórios:
  - `simples`: `prazo` opcional; `recorrencia` e `meta_mensal` vazios.
  - `repetida`: `prazo` (a próxima data) e `recorrencia` obrigatórios; `meta_mensal` vazio.
  - `meta_mensal`: `meta_mensal` (1–31) obrigatório; `prazo` e `recorrencia` vazios.
  - O tipo pode ser trocado na edição; o novo tipo é validado pelas regras acima. Execuções já registradas são mantidas.
- **RN-22** Tarefa **simples**: ir para `concluida` grava `concluida_em = agora`; sair de `concluida` limpa `concluida_em`.
- **RN-23** Tarefa **repetida**: "Concluir" (botão, checkbox ou arrastar para Concluída) faz, numa transação:
  1. registra execução (`data = hoje`, `prazo_referencia = prazo atual`);
  2. `prazo = avancar(recorrencia, prazo atual, hoje)` (RN-32);
  3. `status = pendente`.
  Uma tarefa repetida **nunca permanece** em Concluída.
- **RN-24** Tarefa **meta mensal**:
  - "+1" registra execução com `data = hoje`. Pode passar da meta (ex.: 5/4).
  - "−1" apaga a execução mais recente **do mês de hoje**; sem execuções no mês → erro 409 "Não há execuções neste mês".
  - `progresso_mes` = número de execuções com data no mês de hoje.
  - Coluna **derivada**: `concluida` se `progresso_mes ≥ meta_mensal`, senão `pendente`. No banco, `status` de meta é sempre `pendente`; a API devolve o derivado.
  - Não pode ser arrastada entre colunas (409); pode ser reordenada dentro da coluna em que aparece.
  - Virada de mês zera o progresso automaticamente, pois o cálculo usa o mês de hoje. Não existe job.
  - **Vencimento efetivo** (para avisos e Tarefas de hoje) = último dia do mês de hoje.
- **RN-25** Ordem no quadro:
  - Pendente e Em andamento: `posicao` crescente. Nova tarefa entra no **topo** de Pendente (`posicao` = menor − 1, ou 0).
  - Concluída: `concluida_em` decrescente (posição ignorada); a API devolve as 20 mais recentes e o total.
  - Mover (`POST /tarefas/{id}/mover` com `status` e `indice`): remove a tarefa da coluna de origem, insere na coluna de destino no `indice` (limitado ao tamanho da coluna) e **renumera** `posicao` de 0 a n−1 nas duas colunas, na mesma transação.
- **RN-26** Desfazer conclusão (`POST /tarefas/{id}/desfazer-conclusao`):
  - simples concluída → `status = pendente`, `concluida_em = null`, vai para o topo de Pendente;
  - repetida → apaga a execução mais recente e restaura `prazo = prazo_referencia` dela;
  - meta → igual a "−1".
  - Sem o que desfazer → 409.
- **RN-27** Tarefa **atrasada** = tipo simples ou repetida, não concluída, com `prazo < hoje`, em projeto ativo, não excluída.

## Recorrência (tarefas repetidas e lembretes)

- **RN-30** Formato da regra (JSON):

  ```json
  {"frequencia": "semanal", "intervalo": 1, "dias_semana": [0, 2], "dia_mes": null, "mes": null}
  ```

  - `frequencia`: `diaria` | `semanal` | `mensal` | `anual`.
  - `intervalo`: inteiro 1–365, padrão 1.
  - `dias_semana`: obrigatório e não vazio se `semanal`; valores 0–6 (**0 = segunda … 6 = domingo**, igual a `date.weekday()` do Python); sem repetição, ordenado.
  - `dia_mes`: obrigatório se `mensal` ou `anual`; 1–31.
  - `mes`: obrigatório se `anual`; 1–12.
  - Campos que não se aplicam à frequência devem ser `null`. O front pré-preenche `dia_mes`/`mes` a partir da primeira data.
- **RN-31** A **sequência** de ocorrências é ancorada na data atual do item (`ancora` = `prazo` da tarefa ou `vencimento` do lembrete):
  - `diaria`: `ancora + k·intervalo` dias, k ≥ 0.
  - `semanal`: datas cujo dia da semana está em `dias_semana` e cuja semana (segunda a domingo) é a semana da âncora + `k·intervalo` semanas, k ≥ 0.
  - `mensal`: dia `dia_mes` do mês da âncora + `k·intervalo` meses, k ≥ 0. **Se o mês não tem esse dia, usa o último dia do mês** (31 → 30/abr, 28 ou 29/fev).
  - `anual`: dia `dia_mes` do mês `mes` no ano da âncora + `k·intervalo`, k ≥ 0. 29/02 em ano não bissexto → 28/02.
- **RN-32** `proxima_ocorrencia(regra, ancora, depois_de)` = a primeira data da sequência de RN-31 **estritamente maior** que `depois_de`.
  `avancar(regra, atual, hoje) = proxima_ocorrencia(regra, atual, max(atual, hoje))`.
  Consequência: se o item estava atrasado várias ocorrências, a baixa/conclusão **pula todas as perdidas** e vai para a primeira data futura. Se ainda não venceu, vai para a ocorrência seguinte à atual.
- **RN-33** A primeira data escolhida pelo usuário vale mesmo que não "encaixe" na regra (ex.: regra "toda segunda" e primeira data numa quarta). Depois dela, a sequência segue RN-31.
- **RN-34** `ocorrencias_atrasadas(regra, atual, hoje)`: se `atual > hoje` → 0; senão 1 + quantidade de datas da sequência no intervalo `(atual, hoje]`, limitado a 99. A interface só mostra quando ≥ 2.
- **RN-35** `descrever(regra)` gera o texto em português (calculado no back-end e enviado como `recorrencia_descricao`):

  | Regra | Texto |
  | --- | --- |
  | diária, 1 | "todo dia" |
  | diária, 7 | "a cada 7 dias" |
  | semanal, 1, [0] | "toda segunda" |
  | semanal, 1, [5] | "todo sábado" |
  | semanal, 1, [0, 2, 4] | "toda semana: segunda, quarta e sexta" |
  | semanal, 1, [0..4] | "de segunda a sexta" |
  | semanal, 1, [0..6] | "todo dia" |
  | semanal, 2, [0, 2] | "a cada 2 semanas: segunda e quarta" |
  | mensal, 1, 5 | "todo dia 5" |
  | mensal, 3, 10 | "a cada 3 meses, no dia 10" |
  | mensal, 1, 31 | "todo dia 31 (ou o último dia do mês)" (vale para 29, 30 e 31) |
  | anual, 1, 20/11 | "todo ano em 20/11" |
  | anual, 2, 20/11 | "a cada 2 anos em 20/11" |

  Nomes: segunda, terça, quarta, quinta, sexta, sábado, domingo.
- **RN-36** As funções de recorrência são **puras** (sem banco, sem relógio) e ficam em `app/domain/recorrencia.py`.

## Lembretes

- **RN-40** Campos: `titulo` (1–200), `observacao` (até 2000), `vencimento` (data, obrigatório), `antecedencia_dias` (0–60; padrão = configuração `antecedencia_padrao_lembretes`), `recorrencia` (opcional). Todo lembrete pertence a um projeto.
- **RN-41** Lembrete **ativo** = não excluído, `concluido_em` nulo, em projeto ativo (RN-17).
- **RN-42** **Janela de aviso**: o lembrete ativo aparece nos avisos quando `hoje ≥ vencimento − antecedencia_dias` e continua aparecendo depois do vencimento ("vencido há N dias") até receber baixa. Exemplo: vencimento sexta 16/10, antecedência 3 → aparece em todo acesso de 13/10 em diante.
- **RN-43** **Dar baixa** (`POST /lembretes/{id}/baixa`), numa transação:
  - não recorrente: `concluido_em = agora`; sai dos avisos; vai para "Concluídos" na coluna.
  - recorrente: registra baixa (`ocorrencia = vencimento atual`) e `vencimento = avancar(recorrencia, vencimento, hoje)`. Continua ativo.
  - A baixa pode ser dada a qualquer momento, inclusive antes da janela.
- **RN-44** **Desfazer baixa** (`POST /lembretes/{id}/desfazer-baixa`): não recorrente → `concluido_em = null`; recorrente → apaga a baixa mais recente e restaura `vencimento = ocorrencia` dela. Sem baixa → 409. "Reativar" na seção Concluídos usa este mesmo endpoint.
- **RN-45** A coluna Lembretes lista ativos por `vencimento` crescente, com `dias_restantes`, `na_janela` e `recorrencia_descricao` vindos da API.
- **RN-46** Editar o `vencimento` de um lembrete recorrente muda a âncora da sequência.

## Avisos

- **RN-50** Fontes de aviso (somente de projetos ativos e itens não excluídos):
  1. lembretes ativos dentro da janela (RN-42);
  2. tarefas simples e repetidas não concluídas com `prazo`, quando `hoje ≥ prazo − aviso_tarefas_dias` (configuração, padrão 3);
  3. metas mensais com `progresso_mes < meta_mensal`, quando `hoje ≥ último dia do mês − aviso_tarefas_dias`.
- **RN-51** Ordenação: `dias_restantes` crescente (mais atrasado primeiro); empate → lembrete antes de tarefa; depois `titulo` (ordem alfabética, sem diferenciar maiúsculas).
- **RN-52** O painel aparece ao carregar o app quando há avisos. Mostra 3 e "Ver mais N". "Fechar" oculta até o próximo acesso.
- **RN-53** **Acesso** = carregar a aplicação (abrir ou recarregar). Se o app ficar aberto e a data mudar, ao voltar o foco para a janela o front busca os avisos de novo e reabre o painel se houver itens.
- **RN-54** Ações no painel: lembrete → Dar baixa (RN-43) ou Abrir projeto; tarefa → Concluir (RN-22/23) ou +1 (RN-24) ou Abrir. Após a ação, o item sai da lista e um toast oferece **Desfazer** (RN-26/RN-44).
- **RN-55** Sem avisos, o painel não aparece. O sino mostra o total e reabre o painel.
- **RN-56** Cada aviso traz: `tipo`, `id`, `titulo`, `projeto` (id, nome, cor), `vencimento`, `dias_restantes`, `ocorrencias_atrasadas` (lembretes recorrentes), `meta` (`feitas`, `meta`) para metas.
- **RN-57** O card do projeto mostra a quantidade de avisos daquele projeto (mesmas regras).
- **RN-58** O cálculo de avisos é uma função pura em `app/domain/avisos.py`, que recebe os itens e `hoje` e devolve a lista ordenada.

## Tarefas de hoje

- **RN-60** Lista "Hoje": tarefas simples e repetidas não concluídas com `prazo = hoje`, mais metas incompletas quando hoje é o último dia do mês; somente de projetos ativos.
- **RN-61** "Atrasadas": tarefas de RN-27. Exibidas numa linha recolhida "N atrasadas ›"; a linha some quando N = 0. O estado expandido é lembrado durante a sessão do navegador.
- **RN-62** Ordenação nas duas listas: prioridade (alta, média, baixa), depois nome do projeto, depois título. Atrasadas: prazo mais antigo primeiro.
- **RN-63** Contador da aba = atrasadas + hoje.

## Documentos

- **RN-70** Upload de um ou mais arquivos por vez; cada arquivo até `FRENTES_MAX_UPLOAD_MB` (padrão 50). Qualquer tipo. O nome original é preservado para exibição; no disco o arquivo é salvo como `{uuid}{extensão}` em `dados/anexos/{projeto_id}/`. O nome enviado pelo usuário **nunca** é usado para montar caminho.
- **RN-71** Abrir no navegador (`inline`) somente: PDF, PNG, JPG/JPEG, GIF, WEBP e TXT. Todos os outros tipos (incluindo SVG e HTML) são baixados (`attachment`). Sempre com `X-Content-Type-Options: nosniff`.
- **RN-72** Renomear altera só o nome exibido (1–255 caracteres, sem `/` ou `\`); a extensão original é mantida. Excluir manda para a lixeira.
- **RN-73** Lista ordenada por `criado_em` decrescente.

## Anotações

- **RN-80** Campos: `titulo` (opcional, até 120), `texto` (1–10000, obrigatório), `cor` (`amarelo`, `azul`, `verde`, `rosa`, `roxo`, `cinza`; padrão `amarelo`), `fixada` (padrão `false`).
- **RN-81** Ordem: fixadas primeiro; dentro de cada grupo, `atualizado_em` decrescente.

## Edição em modais

- **RN-85** Modais de criação/edição usam botão **Salvar**. Fechar com alterações não salvas pede confirmação "Descartar alterações?". Ações diretas (arrastar, concluir, +1, dar baixa, fixar) salvam na hora.

## Lixeira

- **RN-90** Excluir projeto, tarefa, lembrete, documento ou anotação = gravar `excluido_em = agora` (exclusão lógica). Itens excluídos não aparecem em nenhuma tela além da Lixeira e não contam em progresso, avisos ou buscas.
- **RN-91** Itens de um projeto excluído ficam ocultos junto com ele e **não** aparecem separadamente na Lixeira. A Lixeira lista: projetos excluídos + itens excluídos cujo projeto não está excluído.
- **RN-92** Restaurar limpa `excluido_em`. Restaurar um projeto traz de volta os itens dele que não tinham sido excluídos individualmente; os excluídos individualmente antes continuam na Lixeira.
- **RN-93** "Excluir agora" e "Esvaziar lixeira" apagam do banco (com os dependentes, via `ON DELETE CASCADE`) e apagam os arquivos físicos dos documentos envolvidos. Os arquivos são apagados **depois** do commit; falha ao apagar arquivo é registrada em log e não desfaz a operação.
- **RN-94** Na inicialização do app, itens com `excluido_em` anterior a `agora − FRENTES_LIXEIRA_DIAS` (padrão 30) são apagados definitivamente, seguindo RN-93.

## Configurações

- **RN-100** Chaves: `aviso_tarefas_dias` (0–60, padrão 3) e `antecedencia_padrao_lembretes` (0–60, padrão 3). Criadas com o padrão na inicialização se não existirem.

## Backup e restauração

- **RN-110** **Exportar** (`GET /api/backup`): gera `frentes-backup-AAAA-MM-DD-HHMM.zip` contendo `frentes.db` (cópia consistente feita pela API de backup do SQLite, nunca cópia direta do arquivo em uso), a pasta `anexos/` e `manifest.json` (`app_versao`, `schema_revisao`, `criado_em`).
- **RN-111** **Restaurar** só pela linha de comando, com o app fechado: `frentes restaurar caminho.zip`. Valida o manifest (revisão de schema igual ou anterior à atual), move os dados atuais para `dados/backups/antes-de-restaurar-{data}/`, extrai o zip e roda as migrations.
- **RN-112** Antes de aplicar migrations na inicialização, se o banco existe e há migration pendente, copia `frentes.db` (pela API de backup do SQLite) para `dados/backups/pre-migracao-{revisao}-{data}.db`, onde `{revisao}` é a revisão atual do banco (`base` se não houver) e `{data}` é `AAAA-MM-DD-HHMM` no fuso de RN-01. Mantém os 5 mais recentes (pela data de modificação do arquivo).

## Busca (Fase 6)

- **RN-120** Busca em: nome e descrição de projetos, título e descrição de tarefas, título e observação de lembretes, título e texto de anotações, nome de documentos. Ignora maiúsculas e acentos. Exclui itens na lixeira. Inclui projetos arquivados (marcados como "Arquivado").
- **RN-121** Implementação portátil: cada tabela pesquisável tem a coluna `busca` com o texto normalizado (minúsculas, sem acentos, espaços simples), atualizada pelo serviço a cada gravação. A consulta usa `LIKE '%termo%'` sobre `busca` com o termo normalizado. Mínimo de 2 caracteres; até 10 resultados por tipo.

## Atalhos (Fase 6)

- **RN-130** `N` = nova tarefa (no projeto aberto; foca a criação rápida); `/` ou `Ctrl+K` = busca; `Esc` = fecha modal/painel. Atalhos de uma tecla não disparam enquanto o foco está num campo de texto.
