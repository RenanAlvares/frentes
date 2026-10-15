"""Tabela `configuracoes` (03-dados)."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.tipos import UTCDateTime


class Configuracao(Base):
    __tablename__ = "configuracoes"

    chave: Mapped[str] = mapped_column(String(50), primary_key=True)
    # Fronteira JSON: cada chave tem seu formato, validado no service (RN-100).
    valor: Mapped[Any] = mapped_column(JSON, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(UTCDateTime)
