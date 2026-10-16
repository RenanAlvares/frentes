import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.clock import Clock, get_clock
from app.db.sessao import get_session
from app.schemas.tarefas import (
    Quadro,
    Tarefa,
    TarefaAtualizar,
    TarefaCriar,
    TarefaDetalhe,
    TarefaMover,
)
from app.services import tarefas as servico

router = APIRouter(tags=["tarefas"])

SessaoDep = Annotated[Session, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]


@router.get("/projetos/{projeto_id}/tarefas", operation_id="obter_quadro", response_model=Quadro)
def obter_quadro(projeto_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Quadro:
    return servico.obter_quadro(sessao, clock, projeto_id)


@router.get(
    "/projetos/{projeto_id}/tarefas/concluidas",
    operation_id="listar_tarefas_concluidas",
    response_model=list[Tarefa],
)
def listar_tarefas_concluidas(
    projeto_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep
) -> list[Tarefa]:
    return servico.listar_concluidas(sessao, clock, projeto_id)


@router.post(
    "/projetos/{projeto_id}/tarefas",
    operation_id="criar_tarefa",
    response_model=Tarefa,
    status_code=status.HTTP_201_CREATED,
)
def criar_tarefa(
    projeto_id: uuid.UUID, dados: TarefaCriar, sessao: SessaoDep, clock: ClockDep
) -> Tarefa:
    return servico.criar_tarefa(sessao, clock, projeto_id, dados)


@router.get("/tarefas/{tarefa_id}", operation_id="obter_tarefa", response_model=TarefaDetalhe)
def obter_tarefa(tarefa_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> TarefaDetalhe:
    return servico.obter_tarefa(sessao, clock, tarefa_id)


@router.patch("/tarefas/{tarefa_id}", operation_id="atualizar_tarefa", response_model=Tarefa)
def atualizar_tarefa(
    tarefa_id: uuid.UUID, dados: TarefaAtualizar, sessao: SessaoDep, clock: ClockDep
) -> Tarefa:
    return servico.atualizar_tarefa(sessao, clock, tarefa_id, dados)


@router.delete(
    "/tarefas/{tarefa_id}", operation_id="excluir_tarefa", status_code=status.HTTP_204_NO_CONTENT
)
def excluir_tarefa(tarefa_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Response:
    servico.excluir_tarefa(sessao, clock, tarefa_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tarefas/{tarefa_id}/mover", operation_id="mover_tarefa", response_model=Quadro)
def mover_tarefa(
    tarefa_id: uuid.UUID, dados: TarefaMover, sessao: SessaoDep, clock: ClockDep
) -> Quadro:
    return servico.mover_tarefa(sessao, clock, tarefa_id, dados)


@router.post("/tarefas/{tarefa_id}/concluir", operation_id="concluir_tarefa", response_model=Tarefa)
def concluir_tarefa(tarefa_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Tarefa:
    return servico.concluir_tarefa(sessao, clock, tarefa_id)


@router.post(
    "/tarefas/{tarefa_id}/desfazer-conclusao",
    operation_id="desfazer_conclusao_tarefa",
    response_model=Tarefa,
)
def desfazer_conclusao_tarefa(tarefa_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Tarefa:
    return servico.desfazer_conclusao(sessao, clock, tarefa_id)
