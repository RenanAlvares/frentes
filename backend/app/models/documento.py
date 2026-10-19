"""Tabela `documentos` (03-dados)."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.tipos import UTCDateTime


class Documento(Base):
    __tablename__ = "documentos"
    __table_args__ = (Index("ix_documentos_projeto_id_criado_em", "projeto_id", "criado_em"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    projeto_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projetos.id", ondelete="CASCADE")
    )
    # Nome exibido: o original do upload (RN-70) ou o do renomear (RN-72). Nunca vira caminho.
    nome: Mapped[str] = mapped_column(String(255))
    extensao: Mapped[str] = mapped_column(String(20))
    mime: Mapped[str] = mapped_column(String(100))
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger)
    chave_storage: Mapped[str] = mapped_column(String(200), unique=True)
    busca: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    atualizado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    excluido_em: Mapped[datetime | None] = mapped_column(UTCDateTime)
