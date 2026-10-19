"""Tabela `anotacoes` (03-dados)."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.tipos import UTCDateTime, enum_texto
from app.domain.enums import CorAnotacao


class Anotacao(Base):
    __tablename__ = "anotacoes"
    __table_args__ = (
        # RN-81: fixadas primeiro, depois `atualizado_em` decrescente.
        Index(
            "ix_anotacoes_projeto_id_fixada_atualizado_em", "projeto_id", "fixada", "atualizado_em"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    projeto_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projetos.id", ondelete="CASCADE")
    )
    titulo: Mapped[str] = mapped_column(String(120))
    texto: Mapped[str] = mapped_column(Text)
    cor: Mapped[CorAnotacao] = mapped_column(enum_texto(CorAnotacao))
    fixada: Mapped[bool]
    busca: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    atualizado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    excluido_em: Mapped[datetime | None] = mapped_column(UTCDateTime)
