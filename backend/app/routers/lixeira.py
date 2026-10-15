import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.sessao import get_session
from app.schemas.lixeira import TipoItemLixeira
from app.services import lixeira as servico

router = APIRouter(prefix="/lixeira", tags=["lixeira"])


@router.post(
    "/{tipo}/{item_id}/restaurar",
    operation_id="restaurar_da_lixeira",
    status_code=status.HTTP_204_NO_CONTENT,
)
def restaurar_da_lixeira(
    tipo: TipoItemLixeira,
    item_id: uuid.UUID,
    sessao: Annotated[Session, Depends(get_session)],
) -> Response:
    servico.restaurar(sessao, tipo, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
