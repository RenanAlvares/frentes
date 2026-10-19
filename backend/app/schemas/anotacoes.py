"""Entrada e saída de anotações (04-api, Anotações; RN-80..81)."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, field_validator

from app.domain.enums import CorAnotacao


def _titulo_valido(valor: str) -> str:
    # RN-80: opcional, até 120.
    valor = valor.strip()
    if len(valor) > 120:
        raise ValueError("Use no máximo 120 caracteres.")
    return valor


def _texto_preenchido(valor: str) -> str:
    # RN-80: obrigatório, 1 a 10000.
    valor = valor.strip()
    if not valor:
        raise ValueError("Escreva o texto da anotação.")
    if len(valor) > 10000:
        raise ValueError("Use no máximo 10000 caracteres.")
    return valor


TituloAnotacao = Annotated[str, AfterValidator(_titulo_valido)]
TextoAnotacao = Annotated[str, AfterValidator(_texto_preenchido)]


class AnotacaoCriar(BaseModel):
    titulo: TituloAnotacao = ""
    texto: TextoAnotacao
    cor: CorAnotacao = CorAnotacao.AMARELO
    fixada: bool = False


class AnotacaoAtualizar(BaseModel):
    """PATCH: só os campos enviados mudam (fixar no card é um PATCH de `fixada`, RN-85)."""

    titulo: TituloAnotacao | None = None
    texto: TextoAnotacao | None = None
    cor: CorAnotacao | None = None
    fixada: bool | None = None

    @field_validator("titulo", "texto", "cor", "fixada", mode="before")
    @classmethod
    def _sem_nulo(cls, valor: object) -> object:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor


class Anotacao(BaseModel):
    id: uuid.UUID
    projeto_id: uuid.UUID
    titulo: str
    texto: str
    cor: CorAnotacao
    fixada: bool
    criado_em: datetime
    atualizado_em: datetime
