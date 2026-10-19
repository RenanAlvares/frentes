import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.clock import Clock, get_clock
from app.db.sessao import get_session
from app.schemas.anotacoes import Anotacao, AnotacaoAtualizar, AnotacaoCriar
from app.services import anotacoes as servico

router = APIRouter(tags=["anotacoes"])

SessaoDep = Annotated[Session, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]


@router.get(
    "/projetos/{projeto_id}/anotacoes",
    operation_id="listar_anotacoes",
    response_model=list[Anotacao],
)
def listar_anotacoes(projeto_id: uuid.UUID, sessao: SessaoDep) -> list[Anotacao]:
    """RN-81: fixadas primeiro, depois as alteradas mais recentemente."""
    return servico.listar_anotacoes(sessao, projeto_id)


@router.post(
    "/projetos/{projeto_id}/anotacoes",
    operation_id="criar_anotacao",
    response_model=Anotacao,
    status_code=status.HTTP_201_CREATED,
)
def criar_anotacao(
    projeto_id: uuid.UUID, dados: AnotacaoCriar, sessao: SessaoDep, clock: ClockDep
) -> Anotacao:
    return servico.criar_anotacao(sessao, clock, projeto_id, dados)


@router.patch(
    "/anotacoes/{anotacao_id}", operation_id="atualizar_anotacao", response_model=Anotacao
)
def atualizar_anotacao(
    anotacao_id: uuid.UUID, dados: AnotacaoAtualizar, sessao: SessaoDep, clock: ClockDep
) -> Anotacao:
    return servico.atualizar_anotacao(sessao, clock, anotacao_id, dados)


@router.delete(
    "/anotacoes/{anotacao_id}",
    operation_id="excluir_anotacao",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_anotacao(anotacao_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Response:
    servico.excluir_anotacao(sessao, clock, anotacao_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
