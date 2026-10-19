import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.clock import Clock, get_clock
from app.config import Settings, get_settings
from app.db.sessao import get_session
from app.schemas.lixeira import ItemLixeira, TipoItemLixeira
from app.services import lixeira as servico
from app.storage.local import Storage, get_storage

router = APIRouter(prefix="/lixeira", tags=["lixeira"])

SessaoDep = Annotated[Session, Depends(get_session)]
StorageDep = Annotated[Storage, Depends(get_storage)]


@router.get("", operation_id="listar_lixeira", response_model=list[ItemLixeira])
def listar_lixeira(
    sessao: SessaoDep,
    clock: Annotated[Clock, Depends(get_clock)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[ItemLixeira]:
    """RN-91: `excluido_em` decrescente."""
    return servico.listar(sessao, clock, settings.lixeira_dias)


@router.delete("", operation_id="esvaziar_lixeira", status_code=status.HTTP_204_NO_CONTENT)
def esvaziar_lixeira(sessao: SessaoDep, storage: StorageDep) -> Response:
    """RN-93: apaga tudo da lixeira definitivamente, com os arquivos."""
    servico.esvaziar(sessao, storage)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{tipo}/{item_id}/restaurar",
    operation_id="restaurar_da_lixeira",
    status_code=status.HTTP_204_NO_CONTENT,
)
def restaurar_da_lixeira(tipo: TipoItemLixeira, item_id: uuid.UUID, sessao: SessaoDep) -> Response:
    servico.restaurar(sessao, tipo, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{tipo}/{item_id}",
    operation_id="excluir_da_lixeira",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_da_lixeira(
    tipo: TipoItemLixeira, item_id: uuid.UUID, sessao: SessaoDep, storage: StorageDep
) -> Response:
    """RN-93: "Excluir agora" (definitivo)."""
    servico.excluir_definitivo(sessao, storage, tipo, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
