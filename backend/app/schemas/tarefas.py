"""Entrada e saída de tarefas (04-api, Tarefas; RN-20, RN-21, RN-25)."""

import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, field_validator

from app.domain.enums import Prioridade, StatusTarefa, TipoTarefa
from app.domain.recorrencia import Recorrencia
from app.schemas.projetos import ProjetoRef


def _titulo_preenchido(valor: str) -> str:
    valor = valor.strip()
    if not valor:
        raise ValueError("Informe o título da tarefa.")
    if len(valor) > 200:
        raise ValueError("Use no máximo 200 caracteres.")
    return valor


TituloTarefa = Annotated[str, AfterValidator(_titulo_preenchido)]
DescricaoTarefa = Annotated[str, Field(max_length=5000)]
# RN-21: as vezes por mês de uma meta.
MetaMensal = Annotated[int, Field(ge=1, le=31)]


class TarefaCriar(BaseModel):
    titulo: TituloTarefa
    descricao: DescricaoTarefa = ""
    prioridade: Prioridade = Prioridade.MEDIA
    tipo: TipoTarefa = TipoTarefa.SIMPLES
    prazo: date | None = None
    recorrencia: Recorrencia | None = None
    meta_mensal: MetaMensal | None = None


class TarefaAtualizar(BaseModel):
    """PATCH: só os campos enviados mudam; `null` só vale para os campos opcionais."""

    titulo: TituloTarefa | None = None
    descricao: DescricaoTarefa | None = None
    prioridade: Prioridade | None = None
    status: StatusTarefa | None = None
    tipo: TipoTarefa | None = None
    prazo: date | None = None
    recorrencia: Recorrencia | None = None
    meta_mensal: MetaMensal | None = None

    @field_validator("titulo", "descricao", "prioridade", "status", "tipo", mode="before")
    @classmethod
    def _sem_nulo(cls, valor: object) -> object:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor


class TarefaMover(BaseModel):
    """RN-25: coluna de destino e posição nela (limitada ao tamanho da coluna)."""

    status: StatusTarefa
    indice: int = Field(ge=0)


class Tarefa(BaseModel):
    id: uuid.UUID
    projeto_id: uuid.UUID
    titulo: str
    descricao: str
    status: StatusTarefa
    prioridade: Prioridade
    tipo: TipoTarefa
    prazo: date | None
    recorrencia: Recorrencia | None
    recorrencia_descricao: str | None
    meta_mensal: int | None
    progresso_mes: int | None
    posicao: int
    concluida_em: datetime | None
    atrasada: bool
    criado_em: datetime
    atualizado_em: datetime


class Execucao(BaseModel):
    data: date
    criado_em: datetime


class TarefaDetalhe(Tarefa):
    execucoes: list[Execucao]


class Quadro(BaseModel):
    pendente: list[Tarefa]
    em_andamento: list[Tarefa]
    concluida: list[Tarefa]
    total_concluidas: int


class TarefaHoje(Tarefa):
    projeto: ProjetoRef


class TarefasHoje(BaseModel):
    """RN-60..62: as duas listas da tela Tarefas de hoje, já ordenadas."""

    atrasadas: list[TarefaHoje]
    hoje: list[TarefaHoje]
