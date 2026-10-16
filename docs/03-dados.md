# 03 — Modelo de dados

Banco: **SQLite** no modo local (arquivo `dados/frentes.db`). O modelo é portátil para PostgreSQL: não usar tipos ou funções exclusivos de um dos dois.

## Convenções

- Nomes de tabelas e colunas em português, sem acento, `snake_case`, tabelas no plural.
- `id`: `sqlalchemy.Uuid` (UUID4 gerado no Python). Em SQLite vira `CHAR(32)`; em PostgreSQL, `UUID`.
- Carimbos de tempo: tipo `UTCDateTime` (TypeDecorator em `app/db/tipos.py`) que grava UTC sem fuso e devolve `datetime` **com** `tzinfo=UTC`. Nunca usar `datetime.now()` sem fuso.
- Datas de negócio: `sa.Date`.
- Enums: `sa.Enum(<Enum Python>, native_enum=False, create_constraint=True, length=20, values_callable=lambda e: [m.value for m in e])` — vira `VARCHAR` + `CHECK` nos dois bancos.
- JSON: `sa.JSON`. Validado por Pydantic antes de gravar.
- Toda tabela principal tem `criado_em`, `atualizado_em` (atualizado pelo serviço) e `excluido_em` (exclusão lógica, RN-90).
- `MetaData(naming_convention=...)` obrigatório, para o Alembic conseguir alterar/remover restrições no SQLite:

  ```python
  NAMING = {
      "ix": "ix_%(column_0_label)s",
      "uq": "uq_%(table_name)s_%(column_0_name)s",
      "ck": "ck_%(table_name)s_%(constraint_name)s",
      "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
      "pk": "pk_%(table_name)s",
  }
  ```

- Chaves estrangeiras com `ondelete="CASCADE"`; no SQLite exige `PRAGMA foreign_keys=ON` em toda conexão (`06-arquitetura.md` §4).
- `busca`: texto normalizado para a busca (RN-121). Criada na Fase 1 em todas as tabelas pesquisáveis, para evitar migration depois; preenchida pelo serviço desde o início.

## Tabelas

### `projetos`

| Coluna | Tipo | Nulo | Padrão / regra |
| --- | --- | --- | --- |
| id | Uuid | não | PK |
| nome | String(100) | não | |
| descricao | Text | não | `''` |
| status | Enum StatusProjeto | não | `em_andamento` |
| cor | Enum CorProjeto | não | `azul` |
| data_inicio | Date | sim | CHECK `data_inicio <= prazo` quando ambos |
| prazo | Date | sim | |
| acompanhar_progresso | Boolean | não | `false` |
| posicao | Integer | não | |
| busca | Text | não | `''` |
| criado_em / atualizado_em | UTCDateTime | não | |
| excluido_em | UTCDateTime | sim | |

Índices: `(excluido_em, status, posicao)`.

### `tarefas`

| Coluna | Tipo | Nulo | Padrão / regra |
| --- | --- | --- | --- |
| id | Uuid | não | PK |
| projeto_id | Uuid FK projetos.id CASCADE | não | |
| titulo | String(200) | não | |
| descricao | Text | não | `''` |
| status | Enum StatusTarefa | não | `pendente` |
| prioridade | Enum Prioridade | não | `media` |
| tipo | Enum TipoTarefa | não | `simples` |
| prazo | Date | sim | |
| recorrencia | JSON | sim | RN-30 |
| meta_mensal | Integer | sim | 1–31 |
| posicao | Integer | não | |
| concluida_em | UTCDateTime | sim | |
| busca | Text | não | `''` |
| criado_em / atualizado_em | UTCDateTime | não | |
| excluido_em | UTCDateTime | sim | |

CHECK `tipo_campos` (RN-21):

```sql
(tipo = 'simples'     AND recorrencia IS NULL AND meta_mensal IS NULL) OR
(tipo = 'repetida'    AND prazo IS NOT NULL AND recorrencia IS NOT NULL AND meta_mensal IS NULL) OR
(tipo = 'meta_mensal' AND prazo IS NULL AND recorrencia IS NULL AND meta_mensal IS NOT NULL AND meta_mensal BETWEEN 1 AND 31)
```

O `meta_mensal IS NOT NULL` é necessário: `NULL BETWEEN 1 AND 31` dá `NULL`, e uma CHECK só rejeita `FALSE`.

Índices: `(projeto_id, status, posicao)`, `(prazo)`.

### `tarefa_execucoes`

Histórico de conclusões de tarefas repetidas e de execuções de metas mensais.

| Coluna | Tipo | Nulo | Regra |
| --- | --- | --- | --- |
| id | Uuid | não | PK |
| tarefa_id | Uuid FK tarefas.id CASCADE | não | |
| data | Date | não | dia da execução (hoje) |
| prazo_referencia | Date | sim | prazo antes de avançar (repetidas), para desfazer |
| criado_em | UTCDateTime | não | desempate de "mais recente" |

Índice: `(tarefa_id, data)`.

### `lembretes`

| Coluna | Tipo | Nulo | Padrão / regra |
| --- | --- | --- | --- |
| id | Uuid | não | PK |
| projeto_id | Uuid FK projetos.id CASCADE | não | |
| titulo | String(200) | não | |
| observacao | Text | não | `''` |
| vencimento | Date | não | ocorrência atual |
| antecedencia_dias | Integer | não | CHECK 0–60 |
| recorrencia | JSON | sim | RN-30 |
| concluido_em | UTCDateTime | sim | só não recorrentes (RN-43) |
| busca | Text | não | `''` |
| criado_em / atualizado_em | UTCDateTime | não | |
| excluido_em | UTCDateTime | sim | |

Índices: `(projeto_id)`, `(vencimento)`.

### `lembrete_baixas`

| Coluna | Tipo | Nulo | Regra |
| --- | --- | --- | --- |
| id | Uuid | não | PK |
| lembrete_id | Uuid FK lembretes.id CASCADE | não | |
| ocorrencia | Date | não | vencimento que recebeu baixa |
| criado_em | UTCDateTime | não | |

Índice: `(lembrete_id, criado_em)`.

### `documentos`

| Coluna | Tipo | Nulo | Regra |
| --- | --- | --- | --- |
| id | Uuid | não | PK |
| projeto_id | Uuid FK projetos.id CASCADE | não | |
| nome | String(255) | não | nome exibido (RN-72) |
| extensao | String(20) | não | minúscula, com ponto (`.pdf`) ou `''` |
| mime | String(100) | não | detectado pela extensão (`mimetypes`) |
| tamanho_bytes | BigInteger | não | |
| chave_storage | String(200) | não | UNIQUE; `{projeto_id}/{uuid}{extensao}` |
| busca | Text | não | `''` |
| criado_em / atualizado_em | UTCDateTime | não | |
| excluido_em | UTCDateTime | sim | |

Índice: `(projeto_id, criado_em)`.

### `anotacoes`

| Coluna | Tipo | Nulo | Padrão |
| --- | --- | --- | --- |
| id | Uuid | não | PK |
| projeto_id | Uuid FK projetos.id CASCADE | não | |
| titulo | String(120) | não | `''` |
| texto | Text | não | |
| cor | Enum CorAnotacao | não | `amarelo` |
| fixada | Boolean | não | `false` |
| busca | Text | não | `''` |
| criado_em / atualizado_em | UTCDateTime | não | |
| excluido_em | UTCDateTime | sim | |

Índice: `(projeto_id, fixada, atualizado_em)`.

### `configuracoes`

| Coluna | Tipo | Nulo | Regra |
| --- | --- | --- | --- |
| chave | String(50) | não | PK |
| valor | JSON | não | |
| atualizado_em | UTCDateTime | não | |

## Enums (Python, `app/domain/enums.py`)

```python
class StatusProjeto(StrEnum): PLANEJADO="planejado"; EM_ANDAMENTO="em_andamento"; AGUARDANDO="aguardando"; CONCLUIDO="concluido"
class CorProjeto(StrEnum): AZUL="azul"; VERDE="verde"; ROXO="roxo"; LARANJA="laranja"; ROSA="rosa"; VERMELHO="vermelho"; CIANO="ciano"; CINZA="cinza"
class StatusTarefa(StrEnum): PENDENTE="pendente"; EM_ANDAMENTO="em_andamento"; CONCLUIDA="concluida"
class Prioridade(StrEnum): BAIXA="baixa"; MEDIA="media"; ALTA="alta"
class TipoTarefa(StrEnum): SIMPLES="simples"; REPETIDA="repetida"; META_MENSAL="meta_mensal"
class CorAnotacao(StrEnum): AMARELO="amarelo"; AZUL="azul"; VERDE="verde"; ROSA="rosa"; ROXO="roxo"; CINZA="cinza"
class Frequencia(StrEnum): DIARIA="diaria"; SEMANAL="semanal"; MENSAL="mensal"; ANUAL="anual"
```

## Regras de consulta

- Todo repositório filtra `excluido_em IS NULL` por padrão. Só a Lixeira consulta excluídos, por funções explícitas (`listar_excluidos`).
- Consultas de itens de projeto (tarefas, lembretes etc.) também exigem o projeto não excluído (join), para respeitar RN-91.
- Proibido SQL específico de banco (ex.: `ILIKE`, `tsvector`, `strftime`). Use expressões do SQLAlchemy.
- Contagens por mês (metas) usam intervalo de datas `[primeiro_dia, último_dia]`, não funções de data do banco.

## Migrations

- Alembic com `render_as_batch=True` e `compare_type=True` (`06-arquitetura.md` §5).
- Uma migration por mudança de modelo, gerada com `--autogenerate` e **revisada à mão** (nomes de restrições, CHECKs, índices).
- Nunca editar uma migration já commitada; criar outra.
