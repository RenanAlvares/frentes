"""Lixeira (04-api, Lixeira; RN-90..94)."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class TipoItemLixeira(StrEnum):
    PROJETO = "projeto"
    TAREFA = "tarefa"
    LEMBRETE = "lembrete"
    DOCUMENTO = "documento"
    ANOTACAO = "anotacao"


class ItemLixeira(BaseModel):
    tipo: TipoItemLixeira
    id: uuid.UUID
    titulo: str
    # Projeto de origem; `null` para o próprio projeto.
    projeto_nome: str | None
    excluido_em: datetime
    # RN-94: a partir daqui, a próxima inicialização apaga definitivamente.
    expira_em: datetime
    # Dias de `hoje` (RN-01) até a data de `expira_em`; 0 = na próxima inicialização.
    dias_para_expirar: int
