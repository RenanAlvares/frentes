from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.clock import ClockFixo, get_clock
from app.config import Settings
from app.main import create_app

HOJE = date(2026, 10, 14)  # quarta-feira


@pytest.fixture
def pasta_dados(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def settings(pasta_dados: Path) -> Settings:
    # Sem .env: os testes não dependem da máquina de quem roda.
    return Settings(
        _env_file=None,
        data_dir=pasta_dados,
        database_url="",
        hoje_simulado=None,
        abrir_navegador=False,
    )


@pytest.fixture
def relogio() -> ClockFixo:
    return ClockFixo(HOJE)


@pytest.fixture
def app(settings: Settings, relogio: ClockFixo) -> FastAPI:
    aplicacao = create_app(settings)
    aplicacao.dependency_overrides[get_clock] = lambda: relogio
    return aplicacao


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as cliente:
        yield cliente
