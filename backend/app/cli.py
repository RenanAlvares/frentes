"""Linha de comando `frentes` (06 §11). `backup` e `restaurar` entram na fase 5."""

import argparse
import socket
import sys
import threading
import time
import webbrowser
from collections.abc import Callable
from typing import Protocol

import uvicorn

from app.config import Settings
from app.main import create_app


class _Servidor(Protocol):
    started: bool
    should_exit: bool


def porta_ocupada(host: str, porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as teste:
        try:
            teste.bind((host, porta))
        except OSError:
            return True
    return False


def abrir_quando_pronto(
    servidor: _Servidor,
    url: str,
    abrir: Callable[[str], object] = webbrowser.open,
    intervalo: float = 0.1,
) -> None:
    """Abre o navegador só depois da inicialização (migrations incluídas) terminar."""
    while not servidor.should_exit:
        if servidor.started:
            abrir(url)
            return
        time.sleep(intervalo)


def iniciar(settings: Settings) -> int:
    url = f"http://{settings.host}:{settings.port}"
    if porta_ocupada(settings.host, settings.port):
        sys.stderr.write(
            f"A porta {settings.port} já está em uso. O Frentes já está aberto? "
            f"Acesse {url} ou defina FRENTES_PORT.\n"
        )
        return 2
    config = uvicorn.Config(create_app(settings), host=settings.host, port=settings.port)
    servidor = uvicorn.Server(config)
    if settings.abrir_navegador:
        threading.Thread(target=abrir_quando_pronto, args=(servidor, url), daemon=True).start()
    # Falha na inicialização (backup/migration) encerra o processo pelo próprio uvicorn.
    servidor.run()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="frentes", description="Gerenciador local de projetos e tarefas."
    )
    comandos = parser.add_subparsers(dest="comando")
    comandos.add_parser("iniciar", help="inicia o app e abre o navegador (padrão)")
    parser.parse_args(argv)
    return iniciar(Settings())


if __name__ == "__main__":
    sys.exit(main())
