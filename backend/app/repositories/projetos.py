"""Consultas de projetos. Excluídos (RN-90) ficam de fora, exceto onde dito."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import StatusProjeto
from app.models.projeto import Projeto

_NAO_EXCLUIDO = Projeto.excluido_em.is_(None)


def obter(sessao: Session, projeto_id: uuid.UUID) -> Projeto | None:
    return sessao.scalar(select(Projeto).where(Projeto.id == projeto_id, _NAO_EXCLUIDO))


def obter_excluido(sessao: Session, projeto_id: uuid.UUID) -> Projeto | None:
    """Só para a Lixeira (03-dados, Regras de consulta)."""
    return sessao.scalar(
        select(Projeto).where(Projeto.id == projeto_id, Projeto.excluido_em.is_not(None))
    )


def listar(sessao: Session, *, arquivados: bool) -> list[Projeto]:
    """RN-12: arquivados = concluídos; senão, os ativos (RN-17). Ordem de RN-15."""
    concluido = Projeto.status == StatusProjeto.CONCLUIDO
    consulta = (
        select(Projeto)
        .where(_NAO_EXCLUIDO, concluido if arquivados else ~concluido)
        .order_by(Projeto.posicao, Projeto.criado_em)
    )
    return list(sessao.scalars(consulta))


def proxima_posicao(sessao: Session) -> int:
    """RN-15: depois de todos, inclusive arquivados e excluídos (que podem voltar)."""
    maior = sessao.scalar(select(func.max(Projeto.posicao)))
    return 0 if maior is None else maior + 1
