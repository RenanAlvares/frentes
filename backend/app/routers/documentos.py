import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.clock import Clock, get_clock
from app.config import Settings, get_settings
from app.db.sessao import get_session
from app.schemas.documentos import Documento, DocumentoAtualizar
from app.services import documentos as servico
from app.storage.local import Storage, get_storage

router = APIRouter(tags=["documentos"])

SessaoDep = Annotated[Session, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]
StorageDep = Annotated[Storage, Depends(get_storage)]


@router.get(
    "/projetos/{projeto_id}/documentos",
    operation_id="listar_documentos",
    response_model=list[Documento],
)
def listar_documentos(projeto_id: uuid.UUID, sessao: SessaoDep) -> list[Documento]:
    """RN-73: mais recentes primeiro."""
    return servico.listar_documentos(sessao, projeto_id)


@router.post(
    "/projetos/{projeto_id}/documentos",
    operation_id="enviar_documentos",
    response_model=list[Documento],
    status_code=status.HTTP_201_CREATED,
)
def enviar_documentos(
    projeto_id: uuid.UUID,
    arquivos: Annotated[list[UploadFile], File(description="Um ou mais arquivos (RN-70).")],
    sessao: SessaoDep,
    clock: ClockDep,
    storage: StorageDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[Documento]:
    enviados = [servico.ArquivoEnviado(nome=a.filename or "", conteudo=a.file) for a in arquivos]
    return servico.enviar_documentos(
        sessao, clock, storage, projeto_id, enviados, settings.max_upload_mb
    )


@router.get(
    "/documentos/{documento_id}/arquivo",
    operation_id="baixar_documento",
    response_class=FileResponse,
    responses={200: {"content": {"application/octet-stream": {}}, "description": "O arquivo."}},
)
def baixar_documento(documento_id: uuid.UUID, sessao: SessaoDep, storage: StorageDep) -> Response:
    """RN-71: `inline` só para os tipos seguros; sempre `nosniff`; nome em `filename*`."""
    arquivo = servico.arquivo_do_documento(sessao, storage, documento_id)
    disposicao = "inline" if arquivo.inline else "attachment"
    return FileResponse(
        arquivo.caminho,
        media_type=arquivo.mime,
        headers={
            "Content-Disposition": f"{disposicao}; filename*=UTF-8''{quote(arquivo.nome, safe='')}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch(
    "/documentos/{documento_id}", operation_id="atualizar_documento", response_model=Documento
)
def atualizar_documento(
    documento_id: uuid.UUID, dados: DocumentoAtualizar, sessao: SessaoDep, clock: ClockDep
) -> Documento:
    """RN-72: renomear mantém a extensão original."""
    return servico.atualizar_documento(sessao, clock, documento_id, dados)


@router.delete(
    "/documentos/{documento_id}",
    operation_id="excluir_documento",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_documento(documento_id: uuid.UUID, sessao: SessaoDep, clock: ClockDep) -> Response:
    servico.excluir_documento(sessao, clock, documento_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
