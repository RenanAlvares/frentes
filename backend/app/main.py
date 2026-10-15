"""Criação do app FastAPI (06 §3)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.config import Settings
from app.db.sessao import criar_engine, criar_session_local
from app.erros import registrar_handlers
from app.routers import sistema


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = criar_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(title="Frentes", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_local = criar_session_local(engine)
    registrar_handlers(app)
    app.include_router(sistema.router, prefix="/api")
    return app


app = create_app()
