import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.clock import Clock, get_clock
from app.db.sessao import get_session
from app.schemas.projetos import (
    Projeto,
    ProjetoAtualizar,
    ProjetoCriar,
    ProjetoResumo,
    ProjetosOrdem,
)
from app.services import projetos as servico

router = APIRouter(prefix="/projetos", tags=["projetos"])

SessaoDep = Annotated[Session, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]


@router.get("", operation_id="listar_projetos", response_model=list[ProjetoResumo])
def listar_projetos(
    sessao: SessaoDep, clock: ClockDep, arquivados: bool = False
) -> list[ProjetoResumo]:
    return servico.listar_projetos(sessao, clock, arquivados=arquivados)


@router.post(
    "",
    operation_id="criar_projeto",
    response_model=Projeto,
    status_code=status.HTTP_201_CREATED,
)
def criar_projeto(dados: ProjetoCriar, sessao: SessaoDep, clock: ClockDep) -> Projeto:
    return servico.criar_projeto(sessao, clock, dados)


@router.put("/ordem", operation_id="reordenar_projetos", status_code=status.HTTP_204_NO_CONTENT)
def reordenar_projetos(dados: ProjetosOrdem, sessao: SessaoDep) -> Response:
    servico.reordenar_projetos(sessao, dados)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{projeto_id}", operation_id="obter_projeto", response_model=Projeto)
def obter_projeto(projeto_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Projeto:
    return servico.obter_projeto(sessao, clock, projeto_id)


@router.patch("/{projeto_id}", operation_id="atualizar_projeto", response_model=Projeto)
def atualizar_projeto(
    projeto_id: uuid.UUID, dados: ProjetoAtualizar, sessao: SessaoDep, clock: ClockDep
) -> Projeto:
    return servico.atualizar_projeto(sessao, clock, projeto_id, dados)


@router.delete(
    "/{projeto_id}", operation_id="excluir_projeto", status_code=status.HTTP_204_NO_CONTENT
)
def excluir_projeto(projeto_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Response:
    servico.excluir_projeto(sessao, clock, projeto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
