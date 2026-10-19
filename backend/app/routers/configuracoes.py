from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.clock import Clock, get_clock
from app.db.sessao import get_session
from app.schemas.configuracoes import Configuracoes, ConfiguracoesAtualizar
from app.services import configuracoes as servico

router = APIRouter(prefix="/configuracoes", tags=["configuracoes"])

SessaoDep = Annotated[Session, Depends(get_session)]


@router.get("", operation_id="obter_configuracoes", response_model=Configuracoes)
def obter_configuracoes(sessao: SessaoDep) -> Configuracoes:
    return servico.obter_configuracoes(sessao)


@router.patch("", operation_id="atualizar_configuracoes", response_model=Configuracoes)
def atualizar_configuracoes(
    dados: ConfiguracoesAtualizar,
    sessao: SessaoDep,
    clock: Annotated[Clock, Depends(get_clock)],
) -> Configuracoes:
    """RN-100: 0 a 60 dias; `aviso_tarefas_dias` muda os avisos na hora."""
    return servico.atualizar_configuracoes(sessao, clock, dados)
