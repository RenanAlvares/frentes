"""LocalStorage (06 §8): blocos, limite sem sobra de arquivo, raiz conferida."""

import io
import uuid
from pathlib import Path

import pytest

from app.erros import ArquivoGrande
from app.storage import local
from app.storage.local import LocalStorage, gerar_chave


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return LocalStorage(tmp_path / "anexos")


def _arquivos(raiz: Path) -> list[Path]:
    return [p for p in raiz.rglob("*") if p.is_file()] if raiz.exists() else []


def test_gerar_chave_usa_projeto_e_uuid() -> None:
    projeto_id = uuid.uuid4()

    pasta, nome = gerar_chave(projeto_id, ".pdf").split("/")

    assert pasta == str(projeto_id)
    assert nome.endswith(".pdf")
    assert uuid.UUID(hex=nome.removesuffix(".pdf"))


def test_salvar_em_blocos(storage: LocalStorage, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local, "BLOCO", 4)
    conteudo = b"0123456789"

    gravados = storage.salvar("p/a.txt", io.BytesIO(conteudo), limite_bytes=10)

    assert gravados == 10
    assert storage.caminho("p/a.txt").read_bytes() == conteudo
    assert _arquivos(storage.raiz) == [storage.caminho("p/a.txt")]


def test_acima_do_limite_nao_deixa_arquivo(
    storage: LocalStorage, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(local, "BLOCO", 4)

    with pytest.raises(ArquivoGrande):
        storage.salvar("p/a.txt", io.BytesIO(b"01234567890"), limite_bytes=10)

    assert _arquivos(storage.raiz) == []


@pytest.mark.parametrize("chave", ["../fora.txt", "p/../../fora.txt", "", "."])
def test_chave_fora_da_raiz_e_recusada(storage: LocalStorage, chave: str) -> None:
    with pytest.raises(ValueError, match="fora do storage"):
        storage.caminho(chave)


def test_apagar(storage: LocalStorage) -> None:
    storage.salvar("p/a.txt", io.BytesIO(b"x"), limite_bytes=1)

    storage.apagar("p/a.txt")
    storage.apagar("p/a.txt")  # não falha se não existir

    assert _arquivos(storage.raiz) == []
