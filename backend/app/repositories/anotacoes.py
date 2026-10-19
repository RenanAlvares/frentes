"""Consultas de anotações. Excluídas (RN-90) e as de projeto excluído (RN-91) ficam de fora."""

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.anotacao import Anotacao
from app.models.projeto import Projeto


def _visiveis() -> Select[Anotacao]:
    return (
        select(Anotacao)
        .join(Projeto, Anotacao.projeto_id == Projeto.id)
        .where(Anotacao.excluido_em.is_(None), Projeto.excluido_em.is_(None))
    )


def obter(sessao: Session, anotacao_id: uuid.UUID) -> Anotacao | None:
    return sessao.scalar(_visiveis().where(Anotacao.id == anotacao_id))


def do_projeto(sessao: Session, projeto_id: uuid.UUID) -> list[Anotacao]:
    """RN-81: fixadas primeiro; em cada grupo, `atualizado_em` decrescente."""
    consulta = (
        _visiveis()
        .where(Anotacao.projeto_id == projeto_id)
        .order_by(Anotacao.fixada.desc(), Anotacao.atualizado_em.desc(), Anotacao.criado_em.desc())
    )
    return list(sessao.scalars(consulta))


def obter_excluida(sessao: Session, anotacao_id: uuid.UUID) -> Anotacao | None:
    """Só para a Lixeira: excluída, com o projeto fora da lixeira (RN-91)."""
    consulta = (
        select(Anotacao)
        .join(Projeto, Anotacao.projeto_id == Projeto.id)
        .where(
            Anotacao.id == anotacao_id,
            Anotacao.excluido_em.is_not(None),
            Projeto.excluido_em.is_(None),
        )
    )
    return sessao.scalar(consulta)
