"""Consultas de lembretes. Excluídos (RN-90) e os de projeto excluído (RN-91) ficam de fora."""

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.lembrete import Lembrete, LembreteBaixa
from app.models.projeto import Projeto


def _visiveis() -> Select[Lembrete]:
    return (
        select(Lembrete)
        .join(Projeto, Lembrete.projeto_id == Projeto.id)
        .where(Lembrete.excluido_em.is_(None), Projeto.excluido_em.is_(None))
    )


def obter(sessao: Session, lembrete_id: uuid.UUID) -> Lembrete | None:
    return sessao.scalar(_visiveis().where(Lembrete.id == lembrete_id))


def ativos(sessao: Session, projeto_id: uuid.UUID) -> list[Lembrete]:
    """RN-45: por `vencimento` crescente."""
    consulta = (
        _visiveis()
        .where(Lembrete.projeto_id == projeto_id, Lembrete.concluido_em.is_(None))
        .order_by(Lembrete.vencimento, Lembrete.criado_em)
    )
    return list(sessao.scalars(consulta))


def concluidos(sessao: Session, projeto_id: uuid.UUID) -> list[Lembrete]:
    """Seção "Concluídos": os que receberam baixa mais recentemente primeiro."""
    consulta = (
        _visiveis()
        .where(Lembrete.projeto_id == projeto_id, Lembrete.concluido_em.is_not(None))
        .order_by(Lembrete.concluido_em.desc())
    )
    return list(sessao.scalars(consulta))


def ultima_baixa(sessao: Session, lembrete_id: uuid.UUID) -> LembreteBaixa | None:
    consulta = (
        select(LembreteBaixa)
        .where(LembreteBaixa.lembrete_id == lembrete_id)
        .order_by(LembreteBaixa.criado_em.desc())
        .limit(1)
    )
    return sessao.scalar(consulta)


def obter_excluido(sessao: Session, lembrete_id: uuid.UUID) -> Lembrete | None:
    """Só para a Lixeira: excluído, com o projeto fora da lixeira (RN-91)."""
    consulta = (
        select(Lembrete)
        .join(Projeto, Lembrete.projeto_id == Projeto.id)
        .where(
            Lembrete.id == lembrete_id,
            Lembrete.excluido_em.is_not(None),
            Projeto.excluido_em.is_(None),
        )
    )
    return sessao.scalar(consulta)
