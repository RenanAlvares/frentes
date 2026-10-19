"""Configurações (04-api, Configurações e backup; RN-100)."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# RN-100: as duas chaves aceitam de 0 a 60 dias.
Dias = Annotated[int, Field(ge=0, le=60)]


class Configuracoes(BaseModel):
    aviso_tarefas_dias: int
    antecedencia_padrao_lembretes: int


class ConfiguracoesAtualizar(BaseModel):
    """PATCH: só as chaves enviadas mudam."""

    aviso_tarefas_dias: Dias | None = None
    antecedencia_padrao_lembretes: Dias | None = None

    @field_validator("aviso_tarefas_dias", "antecedencia_padrao_lembretes", mode="before")
    @classmethod
    def _sem_nulo(cls, valor: object) -> object:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor
