"""Engine, PRAGMAs do SQLite e sessão por requisição (06 §4)."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, create_engine, event, make_url
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

PRAGMAS_SQLITE = (
    "PRAGMA foreign_keys = ON",
    "PRAGMA journal_mode = WAL",
    "PRAGMA busy_timeout = 5000",
    "PRAGMA synchronous = NORMAL",
)


def _aplicar_pragmas(conexao: DBAPIConnection, _registro: ConnectionPoolEntry) -> None:
    cursor = conexao.cursor()
    try:
        for pragma in PRAGMAS_SQLITE:
            cursor.execute(pragma)
    finally:
        cursor.close()


def criar_engine(url: str) -> Engine:
    if make_url(url).get_backend_name() != "sqlite":
        return create_engine(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _aplicar_pragmas)
    return engine


def criar_session_local(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_session(request: Request) -> Iterator[Session]:
    """Uma sessão por requisição; o que o service não confirmou é descartado ao fechar."""
    session_local: sessionmaker[Session] = request.app.state.session_local
    with session_local() as sessao:
        yield sessao
