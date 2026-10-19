from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.sessao import get_session
from app.schemas.busca import ResultadoBusca
from app.services import busca as servico

router = APIRouter(tags=["busca"])


@router.get("/busca", operation_id="buscar", response_model=ResultadoBusca)
def buscar(
    q: Annotated[str, Query(max_length=200)],
    sessao: Annotated[Session, Depends(get_session)],
) -> ResultadoBusca:
    """RN-120..121: ignora acentos e maiúsculas; até 10 por tipo; nada da lixeira."""
    return servico.buscar(sessao, q)
