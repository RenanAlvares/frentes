"""Regras puras de documentos (RN-70..72; 06 §8). Sem banco e sem disco."""

import mimetypes
import re
from pathlib import PurePosixPath

_EXTENSAO = re.compile(r"[a-z0-9.]{1,20}")
# RN-71: só estes abrem no navegador; o resto (inclusive HTML e SVG) é baixado.
_ABREM_NO_NAVEGADOR = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt"})
# Tabela embutida do Python (não lê o registro do Windows): o mesmo mime em qualquer máquina.
_MIMES = mimetypes.MimeTypes()
# A tabela do Python 3.12 ainda não tem os do Office (o 3.13 tem).
_OFFICE = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
for _extensao, _mime in _OFFICE.items():
    _MIMES.add_type(_mime, _extensao)
MIME_PADRAO = "application/octet-stream"


def extensao_segura(nome: str) -> str:
    """06 §8: sufixo minúsculo, com ponto, se for `[a-z0-9.]{1,20}`; senão `''`."""
    extensao = PurePosixPath(nome).suffix.lower()
    return extensao if _EXTENSAO.fullmatch(extensao) else ""


def mime_da_extensao(extensao: str) -> str:
    """03-dados: detectado pela extensão (`mimetypes`)."""
    mime, _codificacao = _MIMES.guess_type(f"arquivo{extensao}")
    return mime or MIME_PADRAO


def abre_no_navegador(extensao: str) -> bool:
    return extensao in _ABREM_NO_NAVEGADOR


def nome_renomeado(novo: str, extensao: str) -> str:
    """RN-72: a extensão original é mantida; se o novo nome já termina nela, fica como digitado."""
    if not extensao or novo.lower().endswith(extensao):
        return novo
    return f"{novo}{extensao}"
