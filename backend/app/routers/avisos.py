from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.clock import Clock, get_clock
from app.db.sessao import get_session
from app.schemas.avisos import Avisos
from app.services import avisos as servico

router = APIRouter(tags=["avisos"])


@router.get("/avisos", operation_id="listar_avisos", response_model=Avisos)
def listar_avisos(
    sessao: Annotated[Session, Depends(get_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> Avisos:
    """RN-50, RN-51: avisos de todos os projetos ativos, mais atrasado primeiro."""
    return servico.listar_avisos(sessao, clock)
