"""Entrada e saída de projetos (04-api, Projetos; RN-10, RN-11)."""

import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import CorProjeto, StatusProjeto


def _nome_preenchido(valor: str) -> str:
    # RN-10: espaços nas pontas são removidos antes de medir.
    valor = valor.strip()
    if not valor:
        raise ValueError("Informe o nome do projeto.")
    if len(valor) > 100:
        raise ValueError("Use no máximo 100 caracteres.")
    return valor


NomeProjeto = Annotated[str, AfterValidator(_nome_preenchido)]
DescricaoProjeto = Annotated[str, Field(max_length=2000)]


class ProjetoCriar(BaseModel):
    nome: NomeProjeto
    descricao: DescricaoProjeto = ""
    status: StatusProjeto = StatusProjeto.EM_ANDAMENTO
    cor: CorProjeto = CorProjeto.AZUL
    data_inicio: date | None = None
    prazo: date | None = None
    acompanhar_progresso: bool = False


class ProjetoAtualizar(BaseModel):
    """PATCH: só os campos enviados mudam; `null` só vale para as datas."""

    nome: NomeProjeto | None = None
    descricao: DescricaoProjeto | None = None
    status: StatusProjeto | None = None
    cor: CorProjeto | None = None
    data_inicio: date | None = None
    prazo: date | None = None
    acompanhar_progresso: bool | None = None

    @field_validator("nome", "descricao", "status", "cor", "acompanhar_progresso", mode="before")
    @classmethod
    def _sem_nulo(cls, valor: object) -> object:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor


class ProjetosOrdem(BaseModel):
    """RN-15: todos os projetos não arquivados, na nova ordem."""

    ids: list[uuid.UUID]


class Progresso(BaseModel):
    concluidas: int
    total: int


class ProjetoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    status: StatusProjeto
    cor: CorProjeto
    prazo: date | None
    acompanhar_progresso: bool
    progresso: Progresso | None
    avisos: int
    posicao: int
    # Em Arquivados, é a data de conclusão (01 §4.7).
    atualizado_em: datetime


class Projeto(ProjetoResumo):
    descricao: str
    data_inicio: date | None
    criado_em: datetime
