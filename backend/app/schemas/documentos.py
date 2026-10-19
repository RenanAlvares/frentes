"""Entrada e saída de documentos (04-api, Documentos; RN-70..73)."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel


class Documento(BaseModel):
    id: uuid.UUID
    projeto_id: uuid.UUID
    nome: str
    extensao: str
    mime: str
    tamanho_bytes: int
    # RN-71: o front decide entre "abrir" e "baixar" por aqui.
    abre_no_navegador: bool
    criado_em: datetime


def _nome_valido(valor: str) -> str:
    # RN-72: 1 a 255 caracteres, sem `/` nem `\`.
    valor = valor.strip()
    if not valor:
        raise ValueError("Informe o nome do documento.")
    if len(valor) > 255:
        raise ValueError("Use no máximo 255 caracteres.")
    if "/" in valor or "\\" in valor:
        raise ValueError("O nome não pode ter / nem \\.")
    return valor


class DocumentoAtualizar(BaseModel):
    nome: Annotated[str, AfterValidator(_nome_valido)]
