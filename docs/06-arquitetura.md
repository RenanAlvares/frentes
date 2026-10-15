# 06 — Arquitetura e back-end

## 1. Visão geral

Um **único processo** (Uvicorn + FastAPI) serve a API em `/api` e o front-end compilado (SPA). Dados em uma pasta local: `frentes.db` (SQLite) e `anexos/`. Nada roda em segundo plano: tudo que depende de data é **calculado no momento da requisição** (avisos, janelas, virada do mês, lixeira expirada na inicialização). Assim, o app pode ficar dias fechado sem perder nada.

```text
Navegador ──HTTP──> Uvicorn/FastAPI ──> routers ──> services ──> repositories ──> SQLAlchemy ──> SQLite
                          │                  │
                          │                  └──> domain (funções puras: recorrência, avisos, textos)
                          └──> static (SPA)       └──> storage (arquivos em dados/anexos)
```

## 2. Stack do back-end

Python 3.12+, gerenciado com **uv** (`pyproject.toml` + `uv.lock` versionado).

| Uso | Pacote |
| --- | --- |
| Web | fastapi, uvicorn[standard], python-multipart |
| Dados | sqlalchemy 2.x, alembic |
| Configuração | pydantic-settings |
| Fuso horário | tzdata (**obrigatório**: o Windows não tem a base de fusos que o `zoneinfo` usa) |
| Pasta de dados padrão | platformdirs |
| Dev | pytest, pytest-cov, httpx, ruff, mypy |

Sem bibliotecas de recorrência (dateutil), de ORM assíncrono ou de filas. Novas dependências exigem aprovação.

## 3. Estrutura de pastas

```text
backend/
  pyproject.toml          # [project.scripts] frentes = "app.cli:main"
  alembic.ini
  migrations/             # env.py + versions/
  app/
    main.py               # create_app(): lifespan, routers, handlers de erro, SPA
    cli.py                # frentes [iniciar] | backup | restaurar <zip>
    config.py             # Settings (pydantic-settings, prefixo FRENTES_)
    clock.py              # Clock: agora_utc(), hoje(); get_clock() como dependência
    erros.py              # ErroApp (NaoEncontrado, Conflito, ArquivoGrande, Validacao) + handlers
    db/
      base.py             # Base declarativa com NAMING (03-dados)
      tipos.py            # UTCDateTime
      sessao.py           # engine, pragmas, SessionLocal, get_session()
      migracoes.py        # backup pré-migração + upgrade head programático
    models/               # um arquivo por tabela
    schemas/              # Pydantic de entrada/saída, um arquivo por recurso
    repositories/         # consultas; filtram excluidos por padrão
    services/             # casos de uso; regras; commit
    domain/
      enums.py
      recorrencia.py      # puro (RN-30..36)
      avisos.py           # puro (RN-50..58)
      textos.py           # normalizar_busca(), etc.
    routers/              # HTTP apenas: valida, chama service, converte resposta
    storage/
      base.py             # Protocol Storage
      local.py            # LocalStorage
    scripts/
      exportar_openapi.py
    static/               # build do front (gerado, no .gitignore)
  tests/
    conftest.py
    unit/                 # domain e funções puras
    api/                  # rotas com TestClient
```

## 4. Camadas e regras

- **routers**: sem regra de negócio e sem consulta direta. Recebem `Session`, `Clock`, `Settings` e `Storage` por `Depends`.
- **services**: uma função por caso de uso (`concluir_tarefa(sessao, clock, tarefa_id)`). Abrem e fecham a transação: terminam com `sessao.commit()`; em erro, a sessão é descartada pelo `get_session()`.
- **repositories**: todas as consultas. Filtro `excluido_em IS NULL` por padrão (RN-90/91).
- **domain**: funções puras, sem SQLAlchemy, sem `datetime.now()`. Recebem `hoje` como parâmetro.
- **schemas**: separar `XCriar`, `XAtualizar` (todos opcionais) e `XResposta`. Validações de RN no schema quando possível (tamanhos, faixas) e no service quando dependem de estado.
- Um service nunca importa um router; um repository nunca importa um service.

### Sessão SQLite

Em `db/sessao.py`, no evento `connect` do engine:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
```

`create_engine(url, connect_args={"check_same_thread": False})`. Rotas síncronas (`def`, não `async def`), que o FastAPI executa em thread pool. `expire_on_commit=False` no `sessionmaker`.

## 5. Migrations (Alembic)

- `env.py` com `render_as_batch=True` (o SQLite não suporta a maioria dos `ALTER TABLE`) e `compare_type=True`, usando o `Base.metadata` com naming convention.
- Na inicialização (`lifespan`): se o banco existe e há migration pendente → backup (RN-112) → `command.upgrade(cfg, "head")`. Banco novo → só `upgrade`.
- Teste obrigatório: `alembic upgrade head` num banco vazio e depois a comparação de metadados (`alembic check` ou `compare_metadata`) sem diferenças.
- `alembic.ini` aponta para `migrations/`; a URL vem do `Settings`, nunca fixa no ini.

## 6. Configuração

`app/config.py` com `pydantic-settings`, prefixo `FRENTES_`, lendo o `.env` da **raiz do repositório** se existir (`env_file = Path(__file__).resolve().parents[2] / ".env"`, independente da pasta de onde o comando roda). Um `FRENTES_DATA_DIR` relativo é resolvido a partir dessa mesma raiz.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `FRENTES_DATA_DIR` | `platformdirs.user_data_dir("Frentes")` | Pasta de dados. No desenvolvimento, `.env` define `dados` (pasta `dados/` na raiz do repositório, ignorada pelo git). |
| `FRENTES_DATABASE_URL` | `sqlite:///{DATA_DIR}/frentes.db` | Trocar para PostgreSQL no futuro. |
| `FRENTES_TIMEZONE` | `America/Sao_Paulo` | RN-01 |
| `FRENTES_HOST` | `127.0.0.1` | Só aceita conexões da própria máquina (não há login). |
| `FRENTES_PORT` | `8765` | Porta do modo de uso (dev usa 8000). |
| `FRENTES_MAX_UPLOAD_MB` | `50` | RN-70 |
| `FRENTES_LIXEIRA_DIAS` | `30` | RN-94 |
| `FRENTES_ABRIR_NAVEGADOR` | `true` | `frentes iniciar` abre o navegador quando o servidor estiver pronto. |
| `FRENTES_HOJE_SIMULADO` | ausente | **Só para teste manual.** Ausente ou string vazia = desligado (o `Settings` converte `""` em `None`). Data `AAAA-MM-DD` que o `Clock` usa como "hoje". Quando definida, `/api/saude` devolve `hoje_simulado: true` e o cabeçalho mostra a faixa "Data simulada: dd/mm/aaaa". |

Caminhos sempre com `pathlib.Path`; nunca concatenar strings com `/` ou `\`.

## 7. Datas e tempo

- `clock.py` define a classe `Clock` com `agora_utc() -> datetime` (com tzinfo UTC) e `hoje() -> date` (data atual em `ZoneInfo(settings.timezone)`).
- Dependência `get_clock()`; os testes a substituem por `ClockFixo(date(2026, 10, 14))` via `app.dependency_overrides`.
- Com `FRENTES_HOJE_SIMULADO` definido, `hoje()` devolve essa data e `agora_utc()` devolve essa data com a hora real do dia (para testes manuais de avisos e virada de mês).
- Proibido no código de aplicação: `date.today()`, `datetime.now()` sem fuso, `datetime.utcnow()`.
- Vencimentos e prazos são `date`; comparações e diferenças entre `date`s (RN-02/03).
- O último dia do mês vem de `calendar.monthrange(ano, mes)[1]`.

## 8. Storage de arquivos

```python
class Storage(Protocol):
    def salvar(self, chave: str, origem: BinaryIO, limite_bytes: int) -> int: ...  # bytes gravados; ArquivoGrande se passar
    def caminho(self, chave: str) -> Path: ...                                    # para FileResponse
    def apagar(self, chave: str) -> None: ...                                     # não falha se não existir
```

- `LocalStorage(raiz=DATA_DIR / "anexos")`. Grava em blocos de 1 MB num arquivo temporário na mesma pasta, contando bytes; ao passar do limite, apaga o temporário e lança `ArquivoGrande`; no fim, `os.replace` para o nome final.
- Chave: `f"{projeto_id}/{uuid4().hex}{extensao}"`. Extensão: `Path(nome).suffix.lower()`, aceita só `[a-z0-9.]{1,20}`, senão `''`.
- `caminho()` resolve o caminho e confirma que está dentro da raiz (defesa contra path traversal).
- Download com `FileResponse`, `Content-Disposition` conforme RN-71 com `filename*=UTF-8''<nome codificado>` e `X-Content-Type-Options: nosniff`.
- Exclusão física de arquivo acontece só depois do commit (RN-93).

## 9. Inicialização (lifespan)

1. Criar `DATA_DIR`, `anexos/`, `backups/`.
2. Backup pré-migração, se necessário (RN-112).
3. `alembic upgrade head`.
4. Criar configurações padrão que faltarem (RN-100).
5. Purgar lixeira expirada (RN-94).
6. Registrar no log: versão, pasta de dados, URL de acesso.

Falha em 2 ou 3 interrompe a inicialização com mensagem clara (o app não sobe com banco em estado incerto).

## 10. Servindo o front-end

- `npm --prefix frontend run build` gera em `backend/app/static/`.
- `main.py` monta `/assets` com `StaticFiles` (cache longo: `Cache-Control: public, max-age=31536000, immutable`). O fallback da SPA fica no handler de 404 (`app/spa.py`): um `GET`/`HEAD` fora de `/api` e `/assets` que não casou com nenhuma rota devolve `index.html` com `Cache-Control: no-cache`. Sem rota catch-all, `/api/*` inexistente dá 404 em qualquer método e o 405 das rotas existentes é preservado.
- Se `static/index.html` não existir (desenvolvimento sem build), o fallback devolve uma página simples dizendo para usar `npm run dev` ou gerar o build.
- Em desenvolvimento, o Vite (porta 5173) faz proxy de `/api` para `127.0.0.1:8000`. Não há CORS em nenhum modo.

## 11. Execução

| Modo | Comandos |
| --- | --- |
| Desenvolvimento | terminal 1: `uv run --directory backend uvicorn app.main:app --reload --port 8000` · terminal 2: `npm --prefix frontend run dev` → abrir `http://localhost:5173` |
| Uso local | `npm --prefix frontend run build` e depois `uv run --directory backend frentes` → abre `http://127.0.0.1:8765` |
| Backup pela linha de comando | `uv run --directory backend frentes backup` (grava o zip na pasta atual) |
| Restaurar | app fechado: `uv run --directory backend frentes restaurar caminho/do/backup.zip` |

`frentes iniciar`: se a porta estiver ocupada, mostra "A porta 8765 já está em uso. O Frentes já está aberto? Acesse http://127.0.0.1:8765 ou defina FRENTES_PORT." e sai com código 2.

Empacotamento (Fase 7, opcional): PyInstaller em modo `onedir`, incluindo `app/static` e `migrations/`. Executáveis sem assinatura podem ser bloqueados por antivírus no Windows; documentar no README. Alternativa: `uv tool install` a partir do repositório.

## 12. Segurança

- Servidor escuta apenas em `127.0.0.1` (sem login, não pode ficar exposto na rede).
- Toda entrada validada por Pydantic (tamanhos, faixas, enums). Mensagens de erro nunca expõem stack trace.
- React escapa o texto; proibido `dangerouslySetInnerHTML`. Descrições são texto puro.
- Upload: limite por arquivo, nome do usuário nunca vira caminho, conferência de raiz no storage, download com `nosniff` e `attachment` para tipos ativos (HTML, SVG).
- Logs sem conteúdo de anotações, descrições ou arquivos.

## 13. Evolução futura para servidor (não implementar agora)

O que muda para hospedar: `FRENTES_DATABASE_URL` para PostgreSQL (o modelo já é portátil); `S3Storage` implementando o mesmo `Storage`; autenticação ligada e `usuario_id` nas tabelas (migration); `FRENTES_HOST=0.0.0.0` atrás de um proxy com HTTPS. Domain, services e front permanecem.
