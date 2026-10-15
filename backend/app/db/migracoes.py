"""Backup pré-migração (RN-112) e `alembic upgrade head` programático (06 §5, §9)."""

import logging
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, make_url
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"
BACKUPS_MANTIDOS = 5


class FalhaInicializacao(RuntimeError):
    """O banco ficaria em estado incerto: o app não sobe (06 §9)."""


def config_alembic(database_url: str) -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.attributes["database_url"] = database_url
    cfg.attributes["configurar_log"] = False
    return cfg


def caminho_sqlite(database_url: str) -> Path | None:
    """Arquivo do banco, se for SQLite em arquivo; senão `None`."""
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or url.database in (None, "", ":memory:"):
        return None
    return Path(url.database)


def revisao_atual(database_url: str) -> str | None:
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        with engine.connect() as conexao:
            return MigrationContext.configure(conexao).get_current_revision()
    finally:
        engine.dispose()


def revisao_head(cfg: Config) -> str | None:
    return ScriptDirectory.from_config(cfg).get_current_head()


def fazer_backup(banco: Path, pasta: Path, revisao: str | None, agora_local: datetime) -> Path:
    """RN-112: copia o banco para `pre-migracao-{revisao}-{data}.db`; mantém os 5 mais recentes."""
    destino = pasta / f"pre-migracao-{revisao or 'base'}-{agora_local:%Y-%m-%d-%H%M}.db"
    # API de backup do SQLite: cópia consistente, inclusive do que ainda está no WAL.
    with closing(sqlite3.connect(banco)) as origem, closing(sqlite3.connect(destino)) as copia:
        origem.backup(copia)
    existentes = sorted(
        pasta.glob("pre-migracao-*.db"), key=lambda arquivo: arquivo.stat().st_mtime, reverse=True
    )
    for antigo in existentes[BACKUPS_MANTIDOS:]:
        antigo.unlink()
    return destino


def migrar(database_url: str, pasta_backups: Path, agora_local: datetime) -> None:
    """Passos 2 e 3 de 06 §9: backup se o banco existe e há migration pendente; depois `upgrade`."""
    cfg = config_alembic(database_url)
    banco = caminho_sqlite(database_url)
    backup: Path | None = None
    if banco is not None and banco.is_file() and banco.stat().st_size > 0:
        try:
            atual = revisao_atual(database_url)
            if atual != revisao_head(cfg):
                backup = fazer_backup(banco, pasta_backups, atual, agora_local)
                logger.info("Backup pré-migração criado em %s", backup)
        except Exception as erro:
            raise FalhaInicializacao(
                f"Não foi possível fazer o backup do banco antes de atualizá-lo: {erro}. "
                "O app não foi iniciado e o banco não foi alterado."
            ) from erro
    try:
        command.upgrade(cfg, "head")
    except Exception as erro:
        copia = f" Cópia de antes da atualização: {backup}." if backup else ""
        raise FalhaInicializacao(
            f"Falha ao atualizar o banco de dados: {erro}. O app não foi iniciado.{copia}"
        ) from erro
