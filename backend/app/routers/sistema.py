from typing import Annotated

from fastapi import APIRouter, Depends

from app import __version__
from app.clock import Clock, get_clock
from app.config import Settings, get_settings
from app.schemas.sistema import SaudeResposta

router = APIRouter(tags=["sistema"])


@router.get("/saude", operation_id="obter_saude", response_model=SaudeResposta)
def obter_saude(
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> SaudeResposta:
    return SaudeResposta(
        status="ok",
        versao=__version__,
        hoje=clock.hoje(),
        hoje_simulado=settings.hoje_simulado is not None,
        lixeira_dias=settings.lixeira_dias,
    )
