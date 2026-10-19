"""Backup e restauração: RN-110, RN-111 (07 §3.8)."""

import io
import json
import socket
import sqlite3
import zipfile
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import __version__, cli
from app.config import Settings
from app.db.migracoes import FalhaInicializacao, config_alembic, revisao_head
from app.main import create_app
from tests.conftest import criar_projeto

# RN-110


def test_rn110_backup_pela_api(client: TestClient, settings: Settings, tmp_path: Path) -> None:
    projeto_id = criar_projeto(client, nome="Casa")["id"]
    envio = client.post(
        f"/api/projetos/{projeto_id}/documentos", files=[("arquivos", ("a.pdf", b"%PDF"))]
    )
    chave = next(p for p in settings.pasta_anexos.rglob("*") if p.is_file())

    resposta = client.get("/api/backup")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/zip"
    # Relógio dos testes: meio-dia em São Paulo.
    assert resposta.headers["content-disposition"] == (
        'attachment; filename="frentes-backup-2026-10-14-1200.zip"'
    )
    with zipfile.ZipFile(io.BytesIO(resposta.content)) as arquivo_zip:
        nomes = arquivo_zip.namelist()
        assert {"frentes.db", "manifest.json", "anexos/"} <= set(nomes)
        assert f"anexos/{projeto_id}/{chave.name}" in nomes
        assert json.loads(arquivo_zip.read("manifest.json")) == {
            "app_versao": __version__,
            "schema_revisao": revisao_head(config_alembic(settings.database_url)),
            "criado_em": "2026-10-14T15:00:00Z",
        }
        arquivo_zip.extract("frentes.db", tmp_path / "extraido")
    assert envio.status_code == 201
    # O banco do zip abre e tem os dados.
    with closing(sqlite3.connect(tmp_path / "extraido" / "frentes.db")) as conexao:
        assert conexao.execute("SELECT nome FROM projetos").fetchall() == [("Casa",)]


def test_rn110_frentes_backup_grava_na_pasta(
    settings: Settings, tmp_path_factory: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    _preencher(settings, "Casa")
    pasta = tmp_path_factory.mktemp("destino")

    assert cli.backup(settings, pasta) == 0

    (gravado,) = pasta.glob("frentes-backup-*.zip")
    assert capsys.readouterr().out == f"Backup gravado em {gravado}\n"
    with zipfile.ZipFile(gravado) as arquivo_zip:
        assert {"frentes.db", "manifest.json"} <= set(arquivo_zip.namelist())


def test_frentes_backup_sem_banco_avisa(
    settings: Settings, tmp_path_factory: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    pasta = tmp_path_factory.mktemp("destino")

    assert cli.backup(settings, pasta) == 1

    assert "Não foi possível gerar o backup" in capsys.readouterr().err
    assert list(pasta.iterdir()) == []


# RN-111


@pytest.fixture
def settings_fechado(settings: Settings) -> Settings:
    # Porta 0 nunca está "em uso": o app conta como fechado.
    settings.port = 0
    return settings


def _preencher(settings: Settings, nome: str) -> None:
    with TestClient(create_app(settings)) as cliente:
        projeto_id = criar_projeto(cliente, nome=nome)["id"]
        arquivo = (f"{nome}.pdf", f"%PDF {nome}".encode())
        resposta = cliente.post(
            f"/api/projetos/{projeto_id}/documentos", files=[("arquivos", arquivo)]
        )
        assert resposta.status_code == 201, resposta.text


def _gerar_zip(settings: Settings, destino: Path) -> Path:
    with TestClient(create_app(settings)) as cliente:
        destino.write_bytes(cliente.get("/api/backup").content)
    return destino


def _estado(settings: Settings) -> dict[str, Any]:
    """Projetos e o conteúdo dos documentos de cada um, vistos pela API."""
    with TestClient(create_app(settings)) as cliente:
        estado: dict[str, Any] = {}
        for projeto in cliente.get("/api/projetos").json():
            documentos = cliente.get(f"/api/projetos/{projeto['id']}/documentos").json()
            estado[projeto["nome"]] = [
                cliente.get(f"/api/documentos/{d['id']}/arquivo").content for d in documentos
            ]
        return estado


def _anteriores(settings: Settings) -> list[Path]:
    return sorted(settings.pasta_backups.glob("antes-de-restaurar-*"))


@pytest.fixture
def backup_de_antes(settings_fechado: Settings, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Backup com o projeto "Antes"; depois dele, os dados ganham o projeto "Depois"."""
    _preencher(settings_fechado, "Antes")
    zip_ = _gerar_zip(settings_fechado, tmp_path_factory.mktemp("zips") / "backup.zip")
    _preencher(settings_fechado, "Depois")
    return zip_


def test_rn111_restaurar_substitui_os_dados_e_guarda_os_antigos(
    settings_fechado: Settings, backup_de_antes: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.restaurar(settings_fechado, backup_de_antes) == 0

    assert _estado(settings_fechado) == {"Antes": [b"%PDF Antes"]}
    (anteriores,) = _anteriores(settings_fechado)
    assert capsys.readouterr().out == (
        f"Dados restaurados de {backup_de_antes}. "
        f"Os dados anteriores foram guardados em {anteriores}.\n"
    )
    assert (anteriores / "frentes.db").is_file()
    guardados = sorted(p.read_bytes() for p in (anteriores / "anexos").rglob("*") if p.is_file())
    assert guardados == [b"%PDF Antes", b"%PDF Depois"]
    with closing(sqlite3.connect(anteriores / "frentes.db")) as conexao:
        nomes = {nome for (nome,) in conexao.execute("SELECT nome FROM projetos")}
    assert nomes == {"Antes", "Depois"}


def _reescrever(zip_: Path, destino: Path, **trocas: bytes | None) -> Path:
    """Cópia do zip com membros trocados (`None` remove; nomes novos entram)."""
    with zipfile.ZipFile(zip_) as origem, zipfile.ZipFile(destino, "w") as novo:
        for nome in origem.namelist():
            if nome not in trocas:
                novo.writestr(nome, origem.read(nome))
        for nome, conteudo in trocas.items():
            if conteudo is not None:
                novo.writestr(nome, conteudo)
    return destino


def test_rn111_backup_de_revisao_mais_nova_e_recusado(
    settings_fechado: Settings, backup_de_antes: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = {"app_versao": "9.9.9", "schema_revisao": "ffffffffffff", "criado_em": "x"}
    zip_ = _reescrever(
        backup_de_antes,
        backup_de_antes.with_name("nova.zip"),
        **{"manifest.json": json.dumps(manifest).encode()},
    )

    assert cli.restaurar(settings_fechado, zip_) == 1

    assert "versão mais nova do Frentes" in capsys.readouterr().err
    assert _estado(settings_fechado) == {"Antes": [b"%PDF Antes"], "Depois": [b"%PDF Depois"]}
    assert _anteriores(settings_fechado) == []


@pytest.mark.parametrize(
    ("trocas", "mensagem"),
    [
        ({"manifest.json": None}, "não é um backup do Frentes"),
        ({"frentes.db": None}, "não é um backup do Frentes"),
        ({"manifest.json": b"{nao e json"}, "manifest.json do backup está ilegível"),
        ({"../fora.txt": b"x"}, "caminho não permitido"),
        ({"anexos/../../fora.txt": b"x"}, "caminho não permitido"),
        ({"/etc/fora.txt": b"x"}, "caminho não permitido"),
        ({"C:/fora.txt": b"x"}, "caminho não permitido"),
        ({"outra/pasta.txt": b"x"}, "caminho não permitido"),
    ],
    ids=[
        "sem-manifest",
        "sem-banco",
        "manifest-ilegivel",
        "pai",
        "pai-em-anexos",
        "absoluto",
        "drive",
        "fora-de-anexos",
    ],
)
def test_rn111_zip_invalido_nao_altera_nada(
    settings_fechado: Settings,
    backup_de_antes: Path,
    trocas: dict[str, bytes | None],
    mensagem: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    zip_ = _reescrever(backup_de_antes, backup_de_antes.with_name("ruim.zip"), **trocas)

    assert cli.restaurar(settings_fechado, zip_) == 1

    assert mensagem in capsys.readouterr().err
    assert _estado(settings_fechado) == {"Antes": [b"%PDF Antes"], "Depois": [b"%PDF Depois"]}
    assert _anteriores(settings_fechado) == []
    assert not (settings_fechado.data_dir.parent / "fora.txt").exists()


def test_rn111_arquivo_que_nao_e_zip(
    settings_fechado: Settings,
    tmp_path_factory: pytest.TempPathFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    falso = tmp_path_factory.mktemp("zips") / "falso.zip"
    falso.write_text("não sou um zip", encoding="utf-8")

    assert cli.restaurar(settings_fechado, falso) == 1

    assert "não é um zip válido" in capsys.readouterr().err


def test_rn111_falha_no_meio_devolve_os_dados_de_antes(
    settings_fechado: Settings, backup_de_antes: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def falhar(*_argumentos: object) -> None:
        raise FalhaInicializacao("migration quebrada")

    monkeypatch.setattr("app.backup.migrar", falhar)

    assert cli.restaurar(settings_fechado, backup_de_antes) == 1

    monkeypatch.undo()
    assert _estado(settings_fechado) == {"Antes": [b"%PDF Antes"], "Depois": [b"%PDF Depois"]}
    assert _anteriores(settings_fechado) == []


@pytest.fixture
def porta_em_uso() -> Iterator[int]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ocupante:
        ocupante.bind(("127.0.0.1", 0))
        ocupante.listen()
        yield ocupante.getsockname()[1]


def test_rn111_com_o_app_aberto_recusa(
    settings: Settings, porta_em_uso: int, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    settings.port = porta_em_uso

    assert cli.restaurar(settings, tmp_path / "qualquer.zip") == 2

    assert capsys.readouterr().err == (
        f"O Frentes parece estar aberto (a porta {porta_em_uso} está em uso). "
        "Feche o app antes de restaurar.\n"
    )


def test_main_despacha_backup_e_restaurar(monkeypatch: pytest.MonkeyPatch) -> None:
    chamadas: list[tuple[str, Path]] = []
    monkeypatch.setattr(cli, "backup", lambda _s, pasta: chamadas.append(("backup", pasta)) or 0)
    monkeypatch.setattr(
        cli, "restaurar", lambda _s, arquivo: chamadas.append(("restaurar", arquivo)) or 0
    )

    assert cli.main(["backup"]) == 0
    assert cli.main(["restaurar", "copia.zip"]) == 0

    assert chamadas == [("backup", Path.cwd()), ("restaurar", Path("copia.zip"))]
