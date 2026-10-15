"""Criação do app FastAPI (06 §3)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from app import __version__
from app.clock import Clock
from app.config import Settings
from app.db.migracoes import migrar
from app.db.sessao import criar_engine, criar_session_local
from app.erros import registrar_handlers
from app.routers import sistema
from app.schemas.erros import ErroResposta
from app.services import configuracoes

# Todo erro sai no formato de 04-api; "default" também tira do contrato o 422 padrão do FastAPI.
RESPOSTAS_ERRO: dict[int | str, dict[str, Any]] = {
    "default": {"model": ErroResposta, "description": "Erro (04-api, Formato de erro)"},
}


def inicializar(settings: Settings, session_local: sessionmaker[Session]) -> None:
    """Passos 1 a 4 de 06 §9. Falha no backup ou na migration impede o app de subir."""
    clock = Clock(settings.timezone, settings.hoje_simulado)
    for pasta in (settings.data_dir, settings.pasta_anexos, settings.pasta_backups):
        pasta.mkdir(parents=True, exist_ok=True)
    agora_local = clock.agora_utc().astimezone(ZoneInfo(settings.timezone))
    migrar(settings.database_url, settings.pasta_backups, agora_local)
    with session_local() as sessao:
        configuracoes.criar_padroes_faltantes(sessao, clock)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = criar_engine(settings.database_url)
    session_local = criar_session_local(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        inicializar(settings, session_local)
        yield
        engine.dispose()

    app = FastAPI(title="Frentes", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_local = session_local
    registrar_handlers(app)
    app.include_router(sistema.router, prefix="/api", responses=RESPOSTAS_ERRO)
    return app


app = create_app()
