"""Casos de uso da Lixeira (RN-90..94). Por enquanto só restaurar (Desfazer das exclusões)."""

import uuid
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.erros import NaoEncontrado
from app.models.lembrete import Lembrete
from app.models.projeto import Projeto
from app.models.tarefa import Tarefa
from app.repositories import lembretes as repositorio_lembretes
from app.repositories import projetos as repositorio_projetos
from app.repositories import tarefas as repositorio_tarefas
from app.schemas.lixeira import TipoItemLixeira

Item = Projeto | Tarefa | Lembrete

# Cada tipo sabe achar o seu item excluído (itens de projeto excluído ficam de fora, RN-91).
_EXCLUIDOS: dict[TipoItemLixeira, Callable[[Session, uuid.UUID], Item | None]] = {
    TipoItemLixeira.PROJETO: repositorio_projetos.obter_excluido,
    TipoItemLixeira.TAREFA: repositorio_tarefas.obter_excluida,
    TipoItemLixeira.LEMBRETE: repositorio_lembretes.obter_excluido,
}


def restaurar(sessao: Session, tipo: TipoItemLixeira, item_id: uuid.UUID) -> None:
    """RN-92: limpa `excluido_em`; o item volta como estava (posição incluída)."""
    item = _EXCLUIDOS[tipo](sessao, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado na lixeira.")
    item.excluido_em = None
    sessao.commit()
