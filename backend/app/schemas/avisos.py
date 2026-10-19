"""Avisos (04-api, Avisos; RN-56)."""

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.schemas.projetos import ProjetoRef


class MetaDoAviso(BaseModel):
    feitas: int
    meta: int


class Aviso(BaseModel):
    tipo: Literal["lembrete", "tarefa"]
    id: uuid.UUID
    titulo: str
    projeto: ProjetoRef
    vencimento: date
    dias_restantes: int
    ocorrencias_atrasadas: int
    meta: MetaDoAviso | None


class Avisos(BaseModel):
    total: int
    itens: list[Aviso]
