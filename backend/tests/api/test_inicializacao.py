"""Inicialização do app (06 §9): pastas, backup pré-migração, migrations e configurações padrão."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.migracoes import FalhaInicializacao, config_alembic, revisao_atual, revisao_head
from app.main import create_app
from app.models import Configuracao


@pytest.fixture
def pasta_dados(tmp_path: Path) -> Path:
    # Pasta ainda inexistente: a inicialização cria tudo.
    return tmp_path / "dados"


def _iniciar(settings: Settings) -> None:
    with TestClient(create_app(settings)):
        pass


def _banco(settings: Settings) -> Path:
    return settings.data_dir / "frentes.db"


def _executar(settings: Settings, *comandos: str) -> None:
    with closing(sqlite3.connect(_banco(settings))) as conexao:
        for sql in comandos:
            conexao.execute(sql)
        conexao.commit()


def _configuracoes(settings: Settings) -> dict[str, object]:
    engine = create_engine(settings.database_url)
    with Session(engine) as sessao:
        valores = {item.chave: item.valor for item in sessao.scalars(select(Configuracao))}
    engine.dispose()
    return valores


def _na_head(settings: Settings) -> bool:
    head = revisao_head(config_alembic(settings.database_url))
    return revisao_atual(settings.database_url) == head


def test_rn100_inicializacao_com_pasta_vazia_cria_banco_pastas_e_padroes(
    settings: Settings,
) -> None:
    _iniciar(settings)

    assert _banco(settings).is_file()
    assert settings.pasta_anexos.is_dir()
    assert settings.pasta_backups.is_dir()
    assert _na_head(settings)
    assert _configuracoes(settings) == {
        "aviso_tarefas_dias": 3,
        "antecedencia_padrao_lembretes": 3,
    }
    # Banco novo: só upgrade, sem backup (RN-112).
    assert list(settings.pasta_backups.iterdir()) == []


def test_rn100_reinicio_cria_so_as_chaves_que_faltam(settings: Settings) -> None:
    _iniciar(settings)
    _executar(
        settings,
        "UPDATE configuracoes SET valor = '7' WHERE chave = 'aviso_tarefas_dias'",
        "DELETE FROM configuracoes WHERE chave = 'antecedencia_padrao_lembretes'",
    )

    _iniciar(settings)

    assert _configuracoes(settings) == {
        "aviso_tarefas_dias": 7,
        "antecedencia_padrao_lembretes": 3,
    }


def test_rn112_banco_sem_migration_pendente_nao_gera_backup(settings: Settings) -> None:
    _iniciar(settings)
    _iniciar(settings)

    assert list(settings.pasta_backups.iterdir()) == []


def test_rn112_migration_pendente_gera_backup_antes_de_migrar(settings: Settings) -> None:
    _iniciar(settings)
    command.downgrade(config_alembic(settings.database_url), "base")
    _executar(settings, "CREATE TABLE marcador (id INTEGER)")

    _iniciar(settings)

    backups = list(settings.pasta_backups.glob("pre-migracao-base-*.db"))
    assert len(backups) == 1
    with closing(sqlite3.connect(backups[0])) as conexao:
        tabelas = {nome for (nome,) in conexao.execute("SELECT name FROM sqlite_master")}
    # O backup é o banco de antes da migration.
    assert "marcador" in tabelas
    assert "configuracoes" not in tabelas
    assert _na_head(settings)


def test_revisao_desconhecida_impede_a_inicializacao(settings: Settings) -> None:
    _iniciar(settings)
    _executar(settings, "UPDATE alembic_version SET version_num = 'desconhecida'")

    with pytest.raises(FalhaInicializacao, match="Falha ao atualizar o banco"):
        _iniciar(settings)

    assert list(settings.pasta_backups.glob("pre-migracao-desconhecida-*.db"))


def test_banco_ilegivel_impede_a_inicializacao_sem_alterar_o_arquivo(settings: Settings) -> None:
    settings.data_dir.mkdir(parents=True)
    _banco(settings).write_bytes(b"isto nao e um banco sqlite" * 10)

    with pytest.raises(FalhaInicializacao, match="backup do banco"):
        _iniciar(settings)

    assert _banco(settings).read_bytes() == b"isto nao e um banco sqlite" * 10
