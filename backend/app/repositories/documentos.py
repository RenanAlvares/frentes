"""Consultas de documentos. Excluídos (RN-90) e os de projeto excluído (RN-91) ficam de fora."""

import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.documento import Documento
from app.models.projeto import Projeto


def _visiveis() -> Select[Documento]:
    return (
        select(Documento)
        .join(Projeto, Documento.projeto_id == Projeto.id)
        .where(Documento.excluido_em.is_(None), Projeto.excluido_em.is_(None))
    )


def obter(sessao: Session, documento_id: uuid.UUID) -> Documento | None:
    return sessao.scalar(_visiveis().where(Documento.id == documento_id))


def do_projeto(sessao: Session, projeto_id: uuid.UUID) -> list[Documento]:
    """RN-73: `criado_em` decrescente; os enviados juntos, pelo nome."""
    consulta = (
        _visiveis()
        .where(Documento.projeto_id == projeto_id)
        .order_by(Documento.criado_em.desc(), Documento.nome)
    )
    return list(sessao.scalars(consulta))


def obter_excluido(sessao: Session, documento_id: uuid.UUID) -> Documento | None:
    """Só para a Lixeira: excluído, com o projeto fora da lixeira (RN-91)."""
    consulta = (
        select(Documento)
        .join(Projeto, Documento.projeto_id == Projeto.id)
        .where(
            Documento.id == documento_id,
            Documento.excluido_em.is_not(None),
            Projeto.excluido_em.is_(None),
        )
    )
    return sessao.scalar(consulta)
