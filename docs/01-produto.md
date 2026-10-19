# 01 — Produto

## 1. Visão

**Frentes — gestor de projetos e tarefas.** É um gerenciador para quem cuida de várias frentes ao mesmo tempo (um gestor, ou alguém com várias funções). Cada frente é um **projeto**. Ao abrir um projeto, a pessoa vê e gerencia tudo dele num só lugar: tarefas, lembretes, documentos e anotações.

- **Usuário único**, sem login no modo local.
- **Roda localmente** em qualquer computador (Windows, macOS, Linux), sem Docker e sem servidor de banco.
- Interface em **português do Brasil**, pensada para ser óbvia de usar.
- Arquitetura pronta para, no futuro, virar um serviço hospedado sem reescrita (ver `06-arquitetura.md` §12).

## 2. Conceitos

| Conceito | O que é |
| --- | --- |
| Projeto | Uma frente de trabalho. Tem nome, status, cor, datas e, opcionalmente, acompanhamento de progresso. |
| Tarefa | Algo a fazer dentro de um projeto. Pode ser **simples**, **repetida** (volta a cada período) ou **meta mensal** (X vezes por mês). |
| Lembrete | Um aviso com data de vencimento, que aparece a partir de N dias antes até receber baixa. Pode se repetir. |
| Documento | Arquivo anexado ao projeto (PDF, planilha, imagem, qualquer tipo). |
| Anotação | Card de texto livre dentro do projeto, com cor e opção de fixar. |
| Aviso | Item exibido no painel de avisos: um lembrete ou uma tarefa dentro da janela de antecedência. |

## 3. Estrutura de navegação

Cabeçalho fixo em todas as telas:

- À esquerda: nome do app **Frentes**.
- Abas: **Projetos** | **Tarefas de hoje** (com contador vermelho de atrasadas + hoje, oculto quando 0).
- À direita: **sino de avisos** (contador; clique reabre o painel de avisos), **busca** (Fase 6) e **menu** (⋯) com: Arquivados, Lixeira, Configurações, Exportar backup.

Rotas:

| Rota | Tela |
| --- | --- |
| `/` | Projetos (home) |
| `/hoje` | Tarefas de hoje |
| `/projetos/:id` | Projeto aberto |
| `/projetos/:id?tarefa=:tarefaId` | Projeto aberto com o modal da tarefa aberto |
| `/arquivados` | Projetos concluídos |
| `/lixeira` | Lixeira |
| `/configuracoes` | Configurações |

## 4. Telas

### 4.1 Painel de avisos (ao entrar)

Aparece no topo da área de conteúdo, em qualquer rota, sempre que o app é carregado e existe pelo menos um aviso (RN-50 a RN-56). Não bloqueia a tela.

- Título: "Avisos" com o total.
- Lista os **3 primeiros** avisos; se houver mais, botão "Ver mais N" expande a lista toda.
- Cada aviso mostra: ícone do tipo (sino = lembrete, check = tarefa), título, chip do projeto (com a cor do projeto), texto relativo de prazo e ações.
- Texto de prazo em vermelho quando vencido ("vencido há 3 dias"), âmbar quando vence hoje ou amanhã, cinza nos demais.
- Lembrete recorrente com mais de uma ocorrência perdida mostra "· 3 ocorrências".
- Meta mensal mostra o progresso: "2/4 · mês termina em 2 dias".
- Ações: lembrete → **Dar baixa**, **Abrir projeto**; tarefa → **Concluir** (meta mensal: **+1**), **Abrir**.
- Botão **Fechar** (X) oculta o painel até o próximo acesso. O sino continua mostrando o total e reabre o painel.

### 4.2 Projetos (home)

- Grade de cards: 4 colunas em telas largas, 3, 2 e 1 conforme a largura.
- Último card: "+ Novo projeto" (borda tracejada), abre o modal de projeto.
- Card do projeto mostra:
  - faixa fina no topo com a **cor do projeto**;
  - nome;
  - status em chip;
  - prazo, se houver ("Prazo 30/11/2026"; em vermelho se já passou);
  - progresso, **somente se** o acompanhamento estiver ligado: barra + "6/10 tarefas";
  - contador de avisos ativos do projeto, se > 0: "2 avisos" (âmbar).
- Clique no card abre o projeto. Menu ⋯ no card: Editar, Excluir.
- Cards podem ser **arrastados para reordenar** (RN-15).
- Estado vazio (nenhum projeto): ilustração simples, "Crie seu primeiro projeto", botão "Novo projeto".
- Projetos com status **Concluído** não aparecem aqui (RN-12).

### 4.3 Tarefas de hoje

- Linha recolhida no topo: "**3 atrasadas ›**" em vermelho; clique expande a lista de atrasadas. Oculta quando não há atrasadas (RN-61).
- Lista "Hoje": tarefas com prazo hoje, de todos os projetos (RN-60).
- Cada item: checkbox para concluir, título, chip do projeto, ícone de prioridade alta (se alta), indicação "repete" ou "meta 2/4" quando aplicável. Clique no título abre o modal da tarefa.
- Estado vazio: "Nada para hoje. Bom trabalho."

### 4.4 Projeto aberto

Cabeçalho:

- Botão voltar (←), nome, chip de status (clicável para trocar), datas ("Início 01/10 · Prazo 30/11"), menu ⋯ (Editar projeto, Excluir projeto).
- Se o progresso estiver ligado: barra de progresso com "6/10 tarefas".
- Descrição do projeto, se houver, em uma linha (expande ao clicar).

Corpo em três colunas:

| Esquerda | Centro | Direita |
| --- | --- | --- |
| **Lembretes** (âmbar) | **Tarefas** (azul) | **Documentos** (verde) acima, **Anotações** (roxo) abaixo |

Cada área tem um cabeçalho com fundo na cor da área, ícone, nome e botão de adicionar. As cores diferenciam as funcionalidades (ver `05-frontend.md` §5).

**Lembretes**

- Lista ordenada por vencimento. Cada item: título, data, regra de repetição ("a cada 7 dias", "todo dia 5"), texto relativo ("vence em 2 dias") e menu (Editar, Dar baixa, Excluir).
- Itens dentro da janela de aviso ficam destacados (borda âmbar); vencidos com texto vermelho.
- Seção recolhida "Concluídos (N)" com lembretes não recorrentes que receberam baixa (com "Reativar").
- "+ Lembrete" abre o modal de lembrete.

**Tarefas**

- Quadro com três colunas: **Pendente**, **Em andamento**, **Concluída**.
- Campo de criação rápida no topo: digitar o título e Enter cria uma tarefa simples em Pendente, prioridade média. Botão "Mais opções" abre o modal completo.
- Card de tarefa: título, prazo (vermelho se atrasada), ícone de prioridade (alta = vermelho, baixa = cinza; média sem ícone), selo "repete" ou "meta 2/4".
- Arrastar entre colunas muda o status; arrastar dentro da coluna reordena (RN-25).
- Meta mensal não é arrastável entre colunas; tem botões **+1** e **−1** no card (RN-24).
- Coluna Concluída mostra as 20 mais recentes e "Ver todas (N)".

**Documentos**

- Área de soltar arquivos ("Solte arquivos aqui ou clique para enviar"), com barra de progresso por arquivo.
- Lista: ícone pelo tipo, nome, tamanho, data. Clique abre ou baixa (RN-71). Menu: Renomear, Baixar, Excluir.

**Anotações**

- Cards coloridos com título (opcional) e até 4 linhas do texto; fixadas primeiro, com ícone de alfinete.
- Clique abre o modal de anotação. "+ Anotação" cria uma nova.

### 4.5 Modal da tarefa

- Título (editável), chips de **status**, **prioridade** e **prazo**, tipo e regra (se repetida/meta), descrição.
- Rodapé: **Excluir** (à esquerda), **Concluir** / **+1** e **Salvar** (à direita).
- Fechar com alterações não salvas pergunta "Descartar alterações?".
- Repetida: mostra "Próxima: 21/10/2026 · toda segunda" e o histórico das últimas 5 execuções.
- Meta mensal: mostra "2 de 4 neste mês" e as datas das execuções do mês.

### 4.6 Modais de criação/edição

- **Projeto**: nome*, descrição, status, cor (8 opções), data de início, prazo, "Acompanhar progresso" (interruptor).
- **Tarefa**: título*, descrição, prioridade, tipo (Simples / Repetida / Meta mensal); Simples → prazo opcional; Repetida → primeira data* + editor de repetição*; Meta mensal → "Quantas vezes por mês"*.
- **Lembrete**: título*, observação, vencimento*, "Avisar com X dias de antecedência" (padrão da configuração), "Repetir" (interruptor) + editor de repetição.
- **Anotação**: título, texto*, cor (6 opções), fixar.
- **Editor de repetição** (componente único, usado por tarefas e lembretes): "A cada [N] [dias | semanas | meses | anos]"; semanas → seleção dos dias (S T Q Q S S D); meses → "no dia [1–31]" (pré-preenchido com o dia da primeira data); anos → dia e mês da primeira data. Mostra a frase final ("A cada 2 semanas, na segunda e na quarta").

`*` = obrigatório. Erros de validação aparecem abaixo do campo.

### 4.7 Arquivados

Lista de projetos concluídos (nome, cor, data de conclusão = `atualizado_em`). Ações: **Abrir**, **Reabrir** (volta para Em andamento).

### 4.8 Lixeira

- Lista: tipo, nome, projeto de origem, excluído em, "apagado definitivamente em X dias".
- Ações por item: **Restaurar**, **Excluir agora** (com confirmação). Botão geral **Esvaziar lixeira** (com confirmação).
- Aviso no topo: "Itens ficam aqui por 30 dias."

### 4.9 Configurações

- "Avisar tarefas com prazo com quantos dias de antecedência" (0–60, padrão 3).
- "Antecedência padrão de novos lembretes" (0–60, padrão 3).
- Seção Backup: **Exportar backup** (baixa o .zip) e instrução de restauração.
- Versão do app.

## 5. Textos padrão

| Situação | Texto |
| --- | --- |
| Status do projeto | Planejado, Em andamento, Aguardando, Concluído |
| Status da tarefa | Pendente, Em andamento, Concluída |
| Prioridade | Baixa, Média, Alta |
| Tipo de tarefa | Simples, Repetida, Meta mensal |
| Prazo relativo | "vencido há 1 dia", "vencido há N dias", "vence hoje", "vence amanhã", "vence em N dias" |
| Toast após ação | "Tarefa concluída", "Baixa registrada", "Movido para a lixeira" + botão **Desfazer** (6 s) |
| Erro genérico | "Não foi possível concluir a ação. Tente de novo." |

Datas são exibidas como `dd/mm/aaaa` (ou `dd/mm` quando o ano é o atual, nos cards).

## 6. Fora do escopo (por enquanto)

Não implementar sem aprovação: login e múltiplos usuários, compartilhamento, deploy em servidor, aplicativo mobile, notificações push do sistema operacional, tema escuro, captura em linguagem natural, estatísticas, subtarefas/checklist, anexos dentro da tarefa, comentários, integração com calendário.
