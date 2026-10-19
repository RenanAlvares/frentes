"""Consultas e exclusões definitivas da Lixeira (RN-91, RN-93). SQL portátil."""

from collections.abc import Callable
from typing import Any, cast

from sqlalchemy import ColumnElement, CursorResult, Delete, delete, or_, select
from sqlalchemy.orm import Session

from app.models.anotacao import Anotacao
from app.models.documento import Documento
from app.models.lembrete import Lembrete
from app.models.projeto import Projeto
from app.models.tarefa import Tarefa

ItemDeProjeto = Tarefa | Lembrete | Documento | Anotacao
MODELOS_DE_PROJETO: tuple[type[ItemDeProjeto], ...] = (Tarefa, Lembrete, Documento, Anotacao)

# Filtro sobre `excluido_em` de um modelo (ex.: "está na lixeira", "expirou").
Filtro = Callable[[Any], ColumnElement[bool]]


def projetos_excluidos(sessao: Session) -> list[Projeto]:
    return list(sessao.scalars(select(Projeto).where(Projeto.excluido_em.is_not(None))))


def itens_excluidos(
    sessao: Session, modelo: type[ItemDeProjeto]
) -> list[tuple[ItemDeProjeto, str]]:
    """RN-91: só os de projeto fora da lixeira, com o nome do projeto."""
    consulta = (
        select(modelo, Projeto.nome)
        .join(Projeto, modelo.projeto_id == Projeto.id)
        .where(modelo.excluido_em.is_not(None), Projeto.excluido_em.is_(None))
    )
    return [(cast(ItemDeProjeto, item), nome) for item, nome in sessao.execute(consulta)]


def chaves_de_documentos(sessao: Session, condicao: ColumnElement[bool]) -> list[str]:
    return list(sessao.scalars(select(Documento.chave_storage).where(condicao)))


def apagar_item(sessao: Session, modelo: type[ItemDeProjeto] | type[Projeto], item_id: Any) -> None:
    """Apaga a linha; os dependentes saem pelo `ON DELETE CASCADE` (RN-93)."""
    sessao.execute(delete(modelo).where(modelo.id == item_id))


def apagar_onde(sessao: Session, filtro: Filtro) -> tuple[int, list[str]]:
    """Apaga projetos e itens que passam no filtro (com os dependentes).

    Devolve quantas linhas saíram diretamente e as chaves dos arquivos a apagar depois do commit:
    as dos documentos filtrados e as de todos os documentos dos projetos filtrados.
    """
    projetos = select(Projeto.id).where(filtro(Projeto))
    chaves = chaves_de_documentos(
        sessao, or_(filtro(Documento), Documento.projeto_id.in_(projetos))
    )
    apagadas = sum(_executar(sessao, delete(m).where(filtro(m))) for m in MODELOS_DE_PROJETO)
    apagadas += _executar(sessao, delete(Projeto).where(filtro(Projeto)))
    return apagadas, chaves


def _executar(sessao: Session, comando: Delete) -> int:
    # DELETE devolve um CursorResult (com `rowcount`); o tipo genérico de `execute` não diz isso.
    return cast(CursorResult[Any], sessao.execute(comando)).rowcount
