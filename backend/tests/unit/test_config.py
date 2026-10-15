from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import RAIZ_REPOSITORIO, Settings


def _settings(**campos: object) -> Settings:
    return Settings(_env_file=None, **campos)


def test_data_dir_relativo_parte_da_raiz_do_repositorio() -> None:
    settings = _settings(data_dir=Path("dados"))

    assert settings.data_dir == RAIZ_REPOSITORIO / "dados"


def test_database_url_padrao_fica_na_pasta_de_dados(tmp_path: Path) -> None:
    settings = _settings(data_dir=tmp_path, database_url="")

    assert settings.database_url == f"sqlite:///{(tmp_path / 'frentes.db').as_posix()}"


def test_database_url_explicita_e_mantida(tmp_path: Path) -> None:
    settings = _settings(data_dir=tmp_path, database_url="sqlite:///outro.db")

    assert settings.database_url == "sqlite:///outro.db"


def test_le_variaveis_com_prefixo_frentes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRENTES_PORT", "9000")
    monkeypatch.setenv("FRENTES_HOJE_SIMULADO", "2026-10-31")

    settings = _settings()

    assert settings.port == 9000
    assert settings.hoje_simulado == date(2026, 10, 31)


def test_hoje_simulado_vazio_fica_desligado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRENTES_HOJE_SIMULADO", "")

    assert _settings().hoje_simulado is None


def test_padroes_seguros() -> None:
    settings = _settings()

    assert settings.host == "127.0.0.1"
    assert settings.timezone == "America/Sao_Paulo"


def test_fuso_desconhecido_e_recusado() -> None:
    with pytest.raises(ValidationError, match="Fuso horário desconhecido"):
        _settings(timezone="Marte/Olympus")
