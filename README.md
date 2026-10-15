# Frentes

[![CI](https://github.com/RenanAlvares/frentes/actions/workflows/ci.yml/badge.svg)](https://github.com/RenanAlvares/frentes/actions/workflows/ci.yml)

**Gestor de projetos e tarefas** que roda no seu computador. Cada frente de trabalho vira um projeto com tarefas (simples, repetidas ou metas mensais), lembretes com antecedência configurável, documentos e anotações. Ao abrir o app, um painel mostra o que vence nos próximos dias e o que já venceu.

> Status: em desenvolvimento. Acompanhe em [`docs/08-roadmap.md`](docs/08-roadmap.md).

## Destaques técnicos

- **Local-first**: um único processo (FastAPI) serve a API e o front-end (React); dados em SQLite e numa pasta de anexos. Sem Docker, sem servidor de banco.
- **Pronto para servidor**: modelo portátil para PostgreSQL e storage de arquivos atrás de uma interface (troca para S3 sem mexer nas regras).
- **Recorrência e avisos como funções puras**, testadas com relógio fixo, inclusive fim de mês e anos bissextos.
- **Contrato tipado** entre back e front: os tipos TypeScript são gerados do OpenAPI e o CI falha se divergirem.
- **Sem jobs em segundo plano**: avisos, metas e lixeira são calculados no momento do acesso.

## Requisitos

- [uv](https://docs.astral.sh/uv/) (instala o Python automaticamente)
- [Node.js](https://nodejs.org/) LTS
- Git

## Como rodar

```bash
# primeira vez
uv sync --directory backend
npm --prefix frontend install
cp .env.example .env            # Windows: copy .env.example .env

# desenvolvimento (dois terminais)
uv run --directory backend uvicorn app.main:app --reload --port 8000
npm --prefix frontend run dev    # abra http://localhost:5173

# uso no dia a dia
npm --prefix frontend run build
uv run --directory backend frentes   # abre http://127.0.0.1:8765
```

O `frentes` sobe o servidor só em `127.0.0.1` e abre o navegador quando o banco estiver pronto. Se a porta 8765 estiver ocupada (o app já está aberto?), ele avisa e sai; troque com `FRENTES_PORT`.

## Configuração e dados

Todas as variáveis são opcionais e começam com `FRENTES_` (lista em [`.env.example`](.env.example) e em [`docs/06-arquitetura.md`](docs/06-arquitetura.md) §6).

- Com o `.env` copiado do exemplo, os dados ficam em `dados/` na raiz do repositório (ignorada pelo git). Sem `.env`, ficam na pasta de dados do sistema (no Windows, `%LOCALAPPDATA%\Frentes\Frentes`; no Linux, `~/.local/share/Frentes`).
- Na pasta de dados: `frentes.db` (SQLite), `anexos/` e `backups/`. Antes de aplicar uma migration num banco existente, o app guarda uma cópia em `backups/` (mantém as 5 mais recentes).

## Testes e verificação

São as mesmas verificações do CI:

```bash
# back-end
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
uv run --directory backend mypy app
uv run --directory backend pytest

# front-end
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run test
npm --prefix frontend run build

# contrato: depois de mudar rota ou schema, regenere e versione os dois arquivos
uv run --directory backend python -m app.scripts.exportar_openapi ../frontend/openapi.json
npm --prefix frontend run gen:api
```

## Documentação

A especificação completa está em [`docs/`](docs/00-indice.md): produto, regras de negócio, dados, API, front-end, arquitetura, testes, roadmap e decisões.

## Licença

A definir.
