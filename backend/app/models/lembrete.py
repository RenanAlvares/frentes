"""Tabelas `lembretes` e `lembrete_baixas` (03-dados)."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.tipos import UTCDateTime


class Lembrete(Base):
    __tablename__ = "lembretes"
    __table_args__ = (
        # RN-40
        CheckConstraint("antecedencia_dias BETWEEN 0 AND 60", name="antecedencia"),
        Index("ix_lembretes_projeto_id", "projeto_id"),
        Index("ix_lembretes_vencimento", "vencimento"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    projeto_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projetos.id", ondelete="CASCADE")
    )
    titulo: Mapped[str] = mapped_column(String(200))
    observacao: Mapped[str] = mapped_column(Text)
    # A ocorrência atual (RN-43 avança este campo nos recorrentes).
    vencimento: Mapped[date]
    antecedencia_dias: Mapped[int]
    # none_as_null: `None` vira NULL no banco (e não o JSON `null`).
    recorrencia: Mapped[dict[str, Any] | None] = mapped_column(JSON(none_as_null=True))
    # Só não recorrentes recebem `concluido_em` (RN-43).
    concluido_em: Mapped[datetime | None] = mapped_column(UTCDateTime)
    busca: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    atualizado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    excluido_em: Mapped[datetime | None] = mapped_column(UTCDateTime)


class LembreteBaixa(Base):
    """Baixas de lembretes recorrentes: a ocorrência que recebeu baixa (para desfazer, RN-44)."""

    __tablename__ = "lembrete_baixas"
    __table_args__ = (
        Index("ix_lembrete_baixas_lembrete_id_criado_em", "lembrete_id", "criado_em"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lembrete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("lembretes.id", ondelete="CASCADE")
    )
    ocorrencia: Mapped[date]
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime)
