"""Casos de uso da Lixeira (RN-90..94)."""

import logging
import uuid
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.textos import titulo_da_anotacao
from app.erros import NaoEncontrado
from app.models.anotacao import Anotacao
from app.models.documento import Documento
from app.models.lembrete import Lembrete
from app.models.projeto import Projeto
from app.models.tarefa import Tarefa
from app.repositories import anotacoes as repositorio_anotacoes
from app.repositories import documentos as repositorio_documentos
from app.repositories import lembretes as repositorio_lembretes
from app.repositories import lixeira as repositorio
from app.repositories import projetos as repositorio_projetos
from app.repositories import tarefas as repositorio_tarefas
from app.schemas.lixeira import ItemLixeira, TipoItemLixeira
from app.storage.local import Storage

logger = logging.getLogger(__name__)

Item = Projeto | Tarefa | Lembrete | Documento | Anotacao

# Cada tipo sabe achar o seu item excluído (itens de projeto excluído ficam de fora, RN-91).
_EXCLUIDOS: dict[TipoItemLixeira, Callable[[Session, uuid.UUID], Item | None]] = {
    TipoItemLixeira.PROJETO: repositorio_projetos.obter_excluido,
    TipoItemLixeira.TAREFA: repositorio_tarefas.obter_excluida,
    TipoItemLixeira.LEMBRETE: repositorio_lembretes.obter_excluido,
    TipoItemLixeira.DOCUMENTO: repositorio_documentos.obter_excluido,
    TipoItemLixeira.ANOTACAO: repositorio_anotacoes.obter_excluida,
}

_TIPOS_DE_ITEM: dict[type[repositorio.ItemDeProjeto], TipoItemLixeira] = {
    Tarefa: TipoItemLixeira.TAREFA,
    Lembrete: TipoItemLixeira.LEMBRETE,
    Documento: TipoItemLixeira.DOCUMENTO,
    Anotacao: TipoItemLixeira.ANOTACAO,
}


def _titulo(item: repositorio.ItemDeProjeto) -> str:
    if isinstance(item, Documento):
        return item.nome
    if isinstance(item, Anotacao):
        return titulo_da_anotacao(item.titulo, item.texto)
    return item.titulo


def _buscar(sessao: Session, tipo: TipoItemLixeira, item_id: uuid.UUID) -> Item:
    item = _EXCLUIDOS[tipo](sessao, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado na lixeira.")
    return item


def listar(sessao: Session, clock: Clock, dias: int) -> list[ItemLixeira]:
    """RN-91: projetos excluídos + itens excluídos de projetos ativos; recentes primeiro."""
    hoje = clock.hoje()

    def item(
        tipo: TipoItemLixeira, id_: uuid.UUID, titulo: str, projeto: str | None, quando: Any
    ) -> ItemLixeira:
        expira = quando + timedelta(days=dias)
        return ItemLixeira(
            tipo=tipo,
            id=id_,
            titulo=titulo,
            projeto_nome=projeto,
            excluido_em=quando,
            expira_em=expira,
            dias_para_expirar=max(0, (clock.data_local(expira) - hoje).days),
        )

    itens = [
        item(TipoItemLixeira.PROJETO, p.id, p.nome, None, p.excluido_em)
        for p in repositorio.projetos_excluidos(sessao)
    ]
    for modelo in repositorio.MODELOS_DE_PROJETO:
        for excluido, projeto_nome in repositorio.itens_excluidos(sessao, modelo):
            itens.append(
                item(
                    _TIPOS_DE_ITEM[modelo],
                    excluido.id,
                    _titulo(excluido),
                    projeto_nome,
                    excluido.excluido_em,
                )
            )
    return sorted(itens, key=lambda i: i.excluido_em, reverse=True)


def restaurar(sessao: Session, tipo: TipoItemLixeira, item_id: uuid.UUID) -> None:
    """RN-92: limpa `excluido_em`; o item volta como estava (posição incluída).

    Num projeto, os itens excluídos um a um antes continuam na lixeira (têm `excluido_em`).
    """
    item = _buscar(sessao, tipo, item_id)
    item.excluido_em = None
    sessao.commit()


def _apagar_arquivos(storage: Storage, chaves: Iterable[str]) -> None:
    """RN-93: depois do commit; falha vai para o log e não desfaz a exclusão."""
    for chave in chaves:
        try:
            storage.apagar(chave)
        except (OSError, ValueError):
            logger.exception("Não foi possível apagar o arquivo de documento %s", chave)


def excluir_definitivo(
    sessao: Session, storage: Storage, tipo: TipoItemLixeira, item_id: uuid.UUID
) -> None:
    """RN-93: "Excluir agora" de um item da lixeira, com os dependentes e os arquivos."""
    item = _buscar(sessao, tipo, item_id)
    if isinstance(item, Projeto):
        chaves = repositorio.chaves_de_documentos(sessao, Documento.projeto_id == item.id)
    else:
        chaves = [item.chave_storage] if isinstance(item, Documento) else []
    repositorio.apagar_item(sessao, type(item), item.id)
    sessao.commit()
    _apagar_arquivos(storage, chaves)


def esvaziar(sessao: Session, storage: Storage) -> None:
    """RN-93: "Esvaziar lixeira". Projeto excluído leva tudo; dos ativos, só os excluídos."""
    _apagadas, chaves = repositorio.apagar_onde(sessao, lambda m: m.excluido_em.is_not(None))
    sessao.commit()
    _apagar_arquivos(storage, chaves)


def purgar_expirados(sessao: Session, storage: Storage, limite: datetime) -> int:
    """RN-94 (passo 5 de 06 §9): apaga o que foi excluído antes de `limite`. Devolve quantos."""
    apagadas, chaves = repositorio.apagar_onde(
        sessao, lambda m: m.excluido_em.is_not(None) & (m.excluido_em < limite)
    )
    sessao.commit()
    _apagar_arquivos(storage, chaves)
    return apagadas
