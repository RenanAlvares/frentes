"""Busca global (04-api, Busca; RN-120..121)."""

import uuid

from pydantic import BaseModel

from app.schemas.projetos import ProjetoRef


class ItemBusca(BaseModel):
    id: uuid.UUID
    titulo: str
    # O projeto do item (num resultado de projeto, o próprio projeto).
    projeto: ProjetoRef
    # RN-120: projeto concluído (ou item dele) aparece marcado como "Arquivado".
    arquivado: bool


class ResultadoBusca(BaseModel):
    projetos: list[ItemBusca]
    tarefas: list[ItemBusca]
    lembretes: list[ItemBusca]
    anotacoes: list[ItemBusca]
    documentos: list[ItemBusca]
