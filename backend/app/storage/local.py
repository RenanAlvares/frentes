"""Storage de arquivos (06 §8). Só chaves geradas pelo app viram caminho (RN-70)."""

import uuid
from pathlib import Path
from typing import Annotated, BinaryIO, Protocol

from fastapi import Depends

from app.config import Settings, get_settings
from app.erros import ArquivoGrande

BLOCO = 1024 * 1024


class Storage(Protocol):
    def salvar(self, chave: str, origem: BinaryIO, limite_bytes: int) -> int:
        """Bytes gravados; `ArquivoGrande` (sem sobrar arquivo) se passar do limite."""
        ...

    def caminho(self, chave: str) -> Path:
        """Para `FileResponse`."""
        ...

    def apagar(self, chave: str) -> None:
        """Não falha se não existir."""
        ...


def gerar_chave(projeto_id: uuid.UUID, extensao: str) -> str:
    """06 §8: `{projeto_id}/{uuid}{extensao}`; a extensão já vem de `extensao_segura`."""
    return f"{projeto_id}/{uuid.uuid4().hex}{extensao}"


class LocalStorage:
    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz.resolve()

    def caminho(self, chave: str) -> Path:
        # Defesa contra path traversal: o caminho resolvido tem de ficar dentro da raiz.
        caminho = (self.raiz / chave).resolve()
        if caminho == self.raiz or not caminho.is_relative_to(self.raiz):
            raise ValueError(f"Chave fora do storage: {chave!r}")
        return caminho

    def salvar(self, chave: str, origem: BinaryIO, limite_bytes: int) -> int:
        destino = self.caminho(chave)
        destino.parent.mkdir(parents=True, exist_ok=True)
        # Temporário na mesma pasta: o `replace` final (os.replace) é atômico.
        temporario = destino.with_name(f".{destino.name}.parcial")
        gravados = 0
        try:
            with temporario.open("wb") as saida:
                while bloco := origem.read(BLOCO):
                    gravados += len(bloco)
                    if gravados > limite_bytes:
                        raise ArquivoGrande()
                    saida.write(bloco)
            temporario.replace(destino)
        except BaseException:
            temporario.unlink(missing_ok=True)
            raise
        return gravados

    def apagar(self, chave: str) -> None:
        self.caminho(chave).unlink(missing_ok=True)


def get_storage(settings: Annotated[Settings, Depends(get_settings)]) -> Storage:
    return LocalStorage(settings.pasta_anexos)
