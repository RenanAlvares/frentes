"""Backup (RN-110) e restauração (RN-111) dos dados: banco + `anexos/` num zip."""

import json
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path, PurePosixPath

from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError

from app import __version__
from app.clock import Clock
from app.config import Settings
from app.db.migracoes import caminho_sqlite, config_alembic, migrar, revisao_atual

BANCO = "frentes.db"
MANIFEST = "manifest.json"
ANEXOS = "anexos"


class BackupInvalido(ValueError):
    """O arquivo não pode ser restaurado; a mensagem é para o usuário."""


def nome_do_backup(clock: Clock) -> str:
    """RN-110: `frentes-backup-AAAA-MM-DD-HHMM.zip`, no fuso de RN-01."""
    return f"frentes-backup-{clock.agora_local():%Y-%m-%d-%H%M}.zip"


def _banco(settings: Settings) -> Path:
    banco = caminho_sqlite(settings.database_url)
    if banco is None:
        raise ValueError("Backup e restauração só funcionam com o banco SQLite em arquivo.")
    return banco


def gerar_backup(settings: Settings, clock: Clock, destino: Path) -> None:
    """RN-110: grava em `destino` o zip com `frentes.db`, `anexos/` e `manifest.json`."""
    banco = _banco(settings)
    if not banco.is_file():
        raise ValueError(f"Não há banco de dados em {banco} para copiar.")
    manifest = {
        "app_versao": __version__,
        "schema_revisao": revisao_atual(settings.database_url),
        "criado_em": clock.agora_utc().isoformat().replace("+00:00", "Z"),
    }
    with tempfile.TemporaryDirectory() as pasta:
        copia = Path(pasta) / BANCO
        # API de backup do SQLite: cópia consistente mesmo com o app aberto.
        with closing(sqlite3.connect(banco)) as origem, closing(sqlite3.connect(copia)) as alvo:
            origem.backup(alvo)
        with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as arquivo_zip:
            arquivo_zip.write(copia, BANCO)
            arquivo_zip.writestr(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2))
            arquivo_zip.writestr(f"{ANEXOS}/", "")
            for anexo in _anexos(settings.pasta_anexos):
                relativo = anexo.relative_to(settings.pasta_anexos).as_posix()
                arquivo_zip.write(anexo, f"{ANEXOS}/{relativo}")


def _anexos(pasta: Path) -> list[Path]:
    # Temporários de envio em andamento (`.{nome}.parcial`, 06 §8) ficam de fora.
    if not pasta.is_dir():
        return []
    return sorted(p for p in pasta.rglob("*") if p.is_file() and not p.name.startswith("."))


def _caminho_permitido(nome: str) -> bool:
    # O zip vem do usuário: nenhum nome dele pode sair da pasta de dados (06 §12).
    caminho = PurePosixPath(nome)
    if caminho.is_absolute() or ".." in caminho.parts or "\\" in nome or ":" in nome:
        return False
    return nome in (BANCO, MANIFEST) or (len(caminho.parts) > 0 and caminho.parts[0] == ANEXOS)


def _validar(arquivo_zip: zipfile.ZipFile, settings: Settings) -> None:
    nomes = arquivo_zip.namelist()
    for nome in nomes:
        if not _caminho_permitido(nome):
            raise BackupInvalido(f"O backup tem um caminho não permitido: {nome!r}.")
    if BANCO not in nomes or MANIFEST not in nomes:
        raise BackupInvalido(
            "O arquivo não é um backup do Frentes (faltam frentes.db ou manifest.json)."
        )
    try:
        manifest = json.loads(arquivo_zip.read(MANIFEST))
    except ValueError as erro:
        raise BackupInvalido("O manifest.json do backup está ilegível.") from erro
    revisao = manifest.get("schema_revisao") if isinstance(manifest, dict) else ""
    if revisao is None:
        return
    # RN-111: a revisão tem de ser igual ou anterior à atual, ou seja, uma que este app conhece.
    scripts = ScriptDirectory.from_config(config_alembic(settings.database_url))
    try:
        conhecida = isinstance(revisao, str) and scripts.get_revision(revisao) is not None
    except CommandError:
        conhecida = False
    if not conhecida:
        raise BackupInvalido(
            f"O backup é de uma versão mais nova do Frentes (revisão {revisao!r}). "
            "Atualize o app antes de restaurar."
        )


def _pasta_anteriores(settings: Settings, clock: Clock) -> Path:
    base = settings.pasta_backups / f"antes-de-restaurar-{clock.agora_local():%Y-%m-%d-%H%M}"
    pasta, numero = base, 1
    while pasta.exists():
        numero += 1
        pasta = base.with_name(f"{base.name}-{numero}")
    pasta.mkdir(parents=True)
    return pasta


def _extrair(arquivo_zip: zipfile.ZipFile, banco: Path, anexos: Path) -> None:
    banco.parent.mkdir(parents=True, exist_ok=True)
    with arquivo_zip.open(BANCO) as origem, banco.open("wb") as destino:
        shutil.copyfileobj(origem, destino)
    anexos.mkdir(parents=True, exist_ok=True)
    raiz = anexos.resolve()
    for info in arquivo_zip.infolist():
        partes = PurePosixPath(info.filename).parts
        if info.is_dir() or partes[0] != ANEXOS or len(partes) < 2:
            continue
        alvo = raiz.joinpath(*partes[1:]).resolve()
        if not alvo.is_relative_to(raiz):  # defesa extra; `_validar` já recusou
            raise BackupInvalido(f"O backup tem um caminho não permitido: {info.filename!r}.")
        alvo.parent.mkdir(parents=True, exist_ok=True)
        with arquivo_zip.open(info) as origem, alvo.open("wb") as destino:
            shutil.copyfileobj(origem, destino)


def restaurar(settings: Settings, clock: Clock, arquivo: Path) -> Path:
    """RN-111 (com o app fechado): troca os dados pelos do backup e devolve onde ficaram os antigos.

    Os dados atuais vão para `backups/antes-de-restaurar-{data}/`; se algo falhar no meio,
    eles voltam para o lugar.
    """
    banco = _banco(settings)
    anexos = settings.pasta_anexos
    try:
        arquivo_zip = zipfile.ZipFile(arquivo)
    except (OSError, zipfile.BadZipFile) as erro:
        raise BackupInvalido(f"Não foi possível abrir {arquivo}: não é um zip válido.") from erro
    with arquivo_zip:
        _validar(arquivo_zip, settings)
        anteriores = _pasta_anteriores(settings, clock)
        atuais = [banco, banco.with_name(f"{banco.name}-wal"), banco.with_name(f"{banco.name}-shm")]
        movidos = [p for p in (*atuais, anexos) if p.exists()]
        for caminho in movidos:
            shutil.move(caminho, anteriores / caminho.name)
        try:
            _extrair(arquivo_zip, banco, anexos)
            migrar(settings.database_url, settings.pasta_backups, clock.agora_local())
        except BaseException:
            # Desfaz: tira o que foi extraído e devolve os dados de antes.
            banco.unlink(missing_ok=True)
            shutil.rmtree(anexos, ignore_errors=True)
            for caminho in movidos:
                shutil.move(anteriores / caminho.name, caminho)
            shutil.rmtree(anteriores, ignore_errors=True)
            raise
    return anteriores
