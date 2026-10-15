"""Comando `frentes` (06 §11)."""

import socket
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from app import cli
from app.config import Settings


@pytest.fixture
def porta_em_uso() -> Iterator[int]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ocupante:
        ocupante.bind(("127.0.0.1", 0))
        ocupante.listen()
        yield ocupante.getsockname()[1]


def test_porta_ocupada_avisa_e_sai_com_codigo_2(
    porta_em_uso: int, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    settings = Settings(_env_file=None, data_dir=tmp_path, port=porta_em_uso)

    assert cli.iniciar(settings) == 2

    assert capsys.readouterr().err == (
        f"A porta {porta_em_uso} já está em uso. O Frentes já está aberto? "
        f"Acesse http://127.0.0.1:{porta_em_uso} ou defina FRENTES_PORT.\n"
    )


def test_porta_livre_nao_e_ocupada(porta_em_uso: int) -> None:
    assert cli.porta_ocupada("127.0.0.1", porta_em_uso)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as livre:
        livre.bind(("127.0.0.1", 0))
        porta = livre.getsockname()[1]
    assert not cli.porta_ocupada("127.0.0.1", porta)


@pytest.mark.parametrize("argv", [[], ["iniciar"]])
def test_sem_comando_ou_iniciar_inicia_o_app(
    argv: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    chamadas: list[Settings] = []
    monkeypatch.setattr(cli, "iniciar", lambda settings: chamadas.append(settings) or 0)

    assert cli.main(argv) == 0
    assert len(chamadas) == 1


@dataclass
class ServidorFalso:
    """Fica pronto depois de `passos_ate_iniciar` consultas a `started`."""

    passos_ate_iniciar: int
    should_exit: bool = False

    @property
    def started(self) -> bool:
        self.passos_ate_iniciar -= 1
        return self.passos_ate_iniciar < 0


def test_abre_o_navegador_so_depois_da_inicializacao() -> None:
    servidor = ServidorFalso(passos_ate_iniciar=3)
    abertas: list[str] = []

    cli.abrir_quando_pronto(servidor, "http://127.0.0.1:8765", abertas.append, intervalo=0)

    assert abertas == ["http://127.0.0.1:8765"]
    assert servidor.passos_ate_iniciar < 0


def test_nao_abre_o_navegador_se_o_servidor_encerrou() -> None:
    servidor = ServidorFalso(passos_ate_iniciar=10**6, should_exit=True)
    abertas: list[str] = []

    cli.abrir_quando_pronto(servidor, "http://127.0.0.1:8765", abertas.append, intervalo=0)

    assert abertas == []
