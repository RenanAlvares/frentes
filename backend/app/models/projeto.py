"""Tabela `projetos` (03-dados)."""

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.tipos import UTCDateTime, enum_texto
from app.domain.enums import CorProjeto, StatusProjeto


class Projeto(Base):
    __tablename__ = "projetos"
    __table_args__ = (
        # RN-16
        CheckConstraint(
            "data_inicio IS NULL OR prazo IS NULL OR data_inicio <= prazo", name="datas"
        ),
        Index("ix_projetos_excluido_em_status_posicao", "excluido_em", "status", "posicao"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[str] = mapped_column(Text)
    status: Mapped[StatusProjeto] = mapped_column(enum_texto(StatusProjeto))
    cor: Mapped[CorProjeto] = mapped_column(enum_texto(CorProjeto))
    data_inicio: Mapped[date | None]
    prazo: Mapped[date | None]
    acompanhar_progresso: Mapped[bool]
    posicao: Mapped[int]
    busca: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    atualizado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    excluido_em: Mapped[datetime | None] = mapped_column(UTCDateTime)
