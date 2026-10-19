"""Linha de comando `frentes` (06 §11): iniciar, backup e restaurar."""

import argparse
import socket
import sys
import threading
import time
import webbrowser
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import uvicorn

from app import backup as servico_backup
from app.clock import Clock
from app.config import Settings
from app.db.migracoes import FalhaInicializacao
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


def backup(settings: Settings, pasta: Path) -> int:
    """`frentes backup`: grava o zip de RN-110 em `pasta` (a pasta atual, 06 §11)."""
    clock = Clock(settings.timezone, settings.hoje_simulado)
    destino = pasta / servico_backup.nome_do_backup(clock)
    try:
        servico_backup.gerar_backup(settings, clock, destino)
    except (OSError, ValueError) as erro:
        destino.unlink(missing_ok=True)
        sys.stderr.write(f"Não foi possível gerar o backup: {erro}\n")
        return 1
    sys.stdout.write(f"Backup gravado em {destino}\n")
    return 0


def restaurar(settings: Settings, arquivo: Path) -> int:
    """`frentes restaurar caminho.zip` (RN-111): só com o app fechado."""
    if porta_ocupada(settings.host, settings.port):
        sys.stderr.write(
            f"O Frentes parece estar aberto (a porta {settings.port} está em uso). "
            "Feche o app antes de restaurar.\n"
        )
        return 2
    clock = Clock(settings.timezone, settings.hoje_simulado)
    try:
        anteriores = servico_backup.restaurar(settings, clock, arquivo)
    except (servico_backup.BackupInvalido, FalhaInicializacao, OSError, ValueError) as erro:
        sys.stderr.write(f"Nada foi alterado. {erro}\n")
        return 1
    sys.stdout.write(
        f"Dados restaurados de {arquivo}. Os dados anteriores foram guardados em {anteriores}.\n"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="frentes", description="Gerenciador local de projetos e tarefas."
    )
    comandos = parser.add_subparsers(dest="comando")
    comandos.add_parser("iniciar", help="inicia o app e abre o navegador (padrão)")
    comandos.add_parser("backup", help="grava um backup (.zip) na pasta atual")
    restaurar_ = comandos.add_parser("restaurar", help="restaura um backup (com o app fechado)")
    restaurar_.add_argument("arquivo", type=Path, help="caminho do .zip gerado pelo backup")
    argumentos = parser.parse_args(argv)
    if argumentos.comando == "backup":
        return backup(Settings(), Path.cwd())
    if argumentos.comando == "restaurar":
        return restaurar(Settings(), argumentos.arquivo)
    return iniciar(Settings())


if __name__ == "__main__":
    sys.exit(main())
