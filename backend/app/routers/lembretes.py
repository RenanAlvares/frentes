import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.clock import Clock, get_clock
from app.db.sessao import get_session
from app.schemas.lembretes import Lembrete, LembreteAtualizar, LembreteCriar, ListaLembretes
from app.services import lembretes as servico

router = APIRouter(tags=["lembretes"])

SessaoDep = Annotated[Session, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]


@router.get(
    "/projetos/{projeto_id}/lembretes",
    operation_id="listar_lembretes",
    response_model=ListaLembretes,
)
def listar_lembretes(projeto_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> ListaLembretes:
    return servico.listar_lembretes(sessao, clock, projeto_id)


@router.post(
    "/projetos/{projeto_id}/lembretes",
    operation_id="criar_lembrete",
    response_model=Lembrete,
    status_code=status.HTTP_201_CREATED,
)
def criar_lembrete(
    projeto_id: uuid.UUID, dados: LembreteCriar, sessao: SessaoDep, clock: ClockDep
) -> Lembrete:
    return servico.criar_lembrete(sessao, clock, projeto_id, dados)


@router.patch(
    "/lembretes/{lembrete_id}", operation_id="atualizar_lembrete", response_model=Lembrete
)
def atualizar_lembrete(
    lembrete_id: uuid.UUID, dados: LembreteAtualizar, sessao: SessaoDep, clock: ClockDep
) -> Lembrete:
    return servico.atualizar_lembrete(sessao, clock, lembrete_id, dados)


@router.delete(
    "/lembretes/{lembrete_id}",
    operation_id="excluir_lembrete",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_lembrete(lembrete_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Response:
    servico.excluir_lembrete(sessao, clock, lembrete_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/lembretes/{lembrete_id}/baixa", operation_id="dar_baixa_lembrete", response_model=Lembrete
)
def dar_baixa_lembrete(lembrete_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Lembrete:
    return servico.dar_baixa(sessao, clock, lembrete_id)


@router.post(
    "/lembretes/{lembrete_id}/desfazer-baixa",
    operation_id="desfazer_baixa_lembrete",
    response_model=Lembrete,
)
def desfazer_baixa_lembrete(lembrete_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Lembrete:
    return servico.desfazer_baixa(sessao, clock, lembrete_id)
