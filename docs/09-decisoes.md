# 09 — Decisões de arquitetura (ADR)

Formato: decisão · motivo · consequência. Para mudar uma decisão, registre uma nova entrada que substitui a anterior.

**ADR-001 · Local-first com SQLite.** O app precisa rodar em qualquer máquina sem instalar banco ou Docker. SQLite é um arquivo, não precisa de servidor e aguenta com folga o volume de um usuário. Consequência: modelo e consultas portáteis (03) para trocar por PostgreSQL só mudando a URL.

**ADR-002 · Processo único servindo API e SPA.** Um comando sobe tudo; sem CORS; uma porta. Consequência: em desenvolvimento, o Vite faz proxy de `/api`.

**ADR-003 · SQLAlchemy síncrono e rotas `def`.** Com SQLite e um usuário, assíncrono só adiciona complexidade (aiosqlite, greenlets) sem ganho. O FastAPI roda rotas síncronas em thread pool.

**ADR-004 · Datas de negócio como `date` e "hoje" calculado no back-end com fuso fixo.** Evita a classe de bugs de UTC × horário local (aviso aparecendo um dia antes). O front nunca converte data de negócio para `Date`. `tzdata` é dependência para funcionar no Windows.

**ADR-005 · Estado derivado no momento da leitura, sem jobs.** Avisos, janelas, progresso de metas e virada de mês são calculados a partir dos dados e de "hoje". O app pode ficar fechado por dias sem perder eventos; não existe estado "esquecido de atualizar".

**ADR-006 · Recorrência própria em vez de RRULE/dateutil.** As regras do produto são poucas (diária, semanal, mensal, anual com intervalo) e precisam de comportamento específico no fim do mês (último dia, sem "grudar" no 28). Funções puras pequenas são mais fáceis de testar e explicar do que mapear para RRULE.

**ADR-007 · Avançar pula ocorrências perdidas.** Dar baixa num lembrete atrasado vai para a próxima data futura, em vez de exigir uma baixa por ocorrência perdida. A quantidade perdida é mostrada ("3 ocorrências") para nada passar despercebido.

**ADR-008 · Ordenação por renumeração em vez de fractional indexing.** Colunas têm poucas dezenas de itens; renumerar a coluna numa transação é simples e sem casos de borda.

**ADR-009 · Tipos do front gerados do OpenAPI.** O contrato tem uma fonte só (schemas Pydantic). O CI falha se o front estiver desatualizado, impedindo divergência silenciosa entre back e front.

**ADR-010 · Sem login no modo local e servidor só em 127.0.0.1.** Um usuário, uma máquina. Login seria atrito sem ganho. Como não há autenticação, o servidor não pode aceitar conexões da rede.

**ADR-011 · Exclusão lógica com purga em 30 dias.** Protege contra exclusão acidental (incluindo de projetos inteiros). A purga roda na inicialização, coerente com ADR-005.

**ADR-012 · Busca por coluna normalizada.** `LIKE` sobre texto sem acentos e em minúsculas funciona igual em SQLite e PostgreSQL. Busca full-text específica de banco fica para o modo servidor, se um dia for necessária.

**ADR-013 · Modais com botão Salvar; ações diretas salvam na hora.** Salvamento automático em formulários complexos (tipo de tarefa, recorrência) cria estados intermediários inválidos. Ações de um clique (arrastar, concluir, baixa) são imediatas e têm Desfazer.

**ADR-014 · Nomes de domínio em português.** O produto, as regras e a interface são em português; manter `projeto`, `tarefa`, `lembrete`, `vencimento` no código evita traduções inconsistentes. Termos técnicos (router, service, repository, schema) ficam em inglês.

**ADR-015 · Metas mensais com status derivado.** O status de uma meta não é gravado; vem da contagem de execuções no mês. Elimina a necessidade de "resetar" metas.
