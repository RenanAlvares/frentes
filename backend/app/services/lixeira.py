"""Casos de uso da Lixeira (RN-90..94). Por enquanto só restaurar (Desfazer das exclusões)."""

import uuid

from sqlalchemy.orm import Session

from app.erros import NaoEncontrado
from app.models.projeto import Projeto
from app.models.tarefa import Tarefa
from app.repositories import projetos as repositorio_projetos
from app.repositories import tarefas as repositorio_tarefas
from app.schemas.lixeira import TipoItemLixeira


def restaurar(sessao: Session, tipo: TipoItemLixeira, item_id: uuid.UUID) -> None:
    """RN-92: limpa `excluido_em`; o item volta como estava (posição incluída)."""
    item: Projeto | Tarefa | None
    if tipo is TipoItemLixeira.PROJETO:
        item = repositorio_projetos.obter_excluido(sessao, item_id)
    else:
        item = repositorio_tarefas.obter_excluida(sessao, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado na lixeira.")
    item.excluido_em = None
    sessao.commit()
