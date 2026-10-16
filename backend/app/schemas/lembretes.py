"""Entrada e saída de lembretes (04-api, Lembretes; RN-40..46)."""

import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, field_validator

from app.domain.recorrencia import Recorrencia


def _titulo_preenchido(valor: str) -> str:
    valor = valor.strip()
    if not valor:
        raise ValueError("Informe o título do lembrete.")
    if len(valor) > 200:
        raise ValueError("Use no máximo 200 caracteres.")
    return valor


TituloLembrete = Annotated[str, AfterValidator(_titulo_preenchido)]
ObservacaoLembrete = Annotated[str, Field(max_length=2000)]
Antecedencia = Annotated[int, Field(ge=0, le=60)]


class LembreteCriar(BaseModel):
    titulo: TituloLembrete
    observacao: ObservacaoLembrete = ""
    vencimento: date
    # Ausente: o padrão da configuração `antecedencia_padrao_lembretes` (RN-40, RN-100).
    antecedencia_dias: Antecedencia | None = None
    recorrencia: Recorrencia | None = None


class LembreteAtualizar(BaseModel):
    """PATCH: só os campos enviados mudam; `recorrencia: null` remove a repetição."""

    titulo: TituloLembrete | None = None
    observacao: ObservacaoLembrete | None = None
    vencimento: date | None = None
    antecedencia_dias: Antecedencia | None = None
    recorrencia: Recorrencia | None = None

    @field_validator("titulo", "observacao", "vencimento", "antecedencia_dias", mode="before")
    @classmethod
    def _sem_nulo(cls, valor: object) -> object:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor


class Lembrete(BaseModel):
    id: uuid.UUID
    projeto_id: uuid.UUID
    titulo: str
    observacao: str
    vencimento: date
    antecedencia_dias: int
    recorrencia: Recorrencia | None
    recorrencia_descricao: str | None
    dias_restantes: int
    na_janela: bool
    ocorrencias_atrasadas: int
    concluido_em: datetime | None
    criado_em: datetime
    atualizado_em: datetime


class ListaLembretes(BaseModel):
    ativos: list[Lembrete]
    concluidos: list[Lembrete]
