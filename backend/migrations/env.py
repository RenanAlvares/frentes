"""Ambiente do Alembic: URL do Settings e batch mode para o SQLite (06 §5)."""

from logging.config import fileConfig
from typing import Any, Literal

from alembic import context
from alembic.autogenerate.api import AutogenContext
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401 (registra as tabelas no Base.metadata)
from app.config import Settings
from app.db.base import Base
from app.db.tipos import UTCDateTime

config = context.config

# Na inicialização do app o logging é do uvicorn; só a linha de comando usa o do alembic.ini.
if config.config_file_name is not None and config.attributes.get("configurar_log", True):
    fileConfig(config.config_file_name)


def _url() -> str:
    """URL passada pela inicialização (db/migracoes.py) ou, na linha de comando, a do Settings."""
    url = config.attributes.get("database_url")
    return url if isinstance(url, str) else Settings().database_url


def _render_item(tipo: str, objeto: Any, _contexto: AutogenContext) -> str | Literal[False]:
    # Migrations não importam app/: no banco, UTCDateTime é um DateTime comum.
    if tipo == "type" and isinstance(objeto, UTCDateTime):
        return "sa.DateTime()"
    return False


OPCOES: dict[str, Any] = {
    "target_metadata": Base.metadata,
    "render_as_batch": True,
    "compare_type": True,
    "render_item": _render_item,
}


def run_migrations_offline() -> None:
    context.configure(url=_url(), literal_binds=True, **OPCOES)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Sem os PRAGMAs do app: o batch mode recria tabelas e não pode disparar foreign_keys.
    engine = create_engine(_url(), poolclass=NullPool)
    with engine.connect() as conexao:
        context.configure(connection=conexao, **OPCOES)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
