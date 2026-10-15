# Frentes

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

## Documentação

A especificação completa está em [`docs/`](docs/00-indice.md): produto, regras de negócio, dados, API, front-end, arquitetura, testes, roadmap e decisões.

## Licença

A definir.
