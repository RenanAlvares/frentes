import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app import backup
from app.clock import Clock, get_clock
from app.config import Settings, get_settings

router = APIRouter(tags=["backup"])


@router.get(
    "/backup",
    operation_id="exportar_backup",
    response_class=FileResponse,
    responses={200: {"content": {"application/zip": {}}, "description": "O zip (RN-110)."}},
)
def exportar_backup(
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> Response:
    """RN-110: `frentes.db` + `anexos/` + `manifest.json`; o temporário sai depois do envio."""
    descritor, nome_temporario = tempfile.mkstemp(suffix=".zip")
    os.close(descritor)
    temporario = Path(nome_temporario)
    try:
        backup.gerar_backup(settings, clock, temporario)
    except BaseException:
        temporario.unlink(missing_ok=True)
        raise
    return FileResponse(
        temporario,
        media_type="application/zip",
        filename=backup.nome_do_backup(clock),
        background=BackgroundTask(temporario.unlink, missing_ok=True),
    )
