"""Tabelas `tarefas` e `tarefa_execucoes` (03-dados)."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.tipos import UTCDateTime, enum_texto
from app.domain.enums import Prioridade, StatusTarefa, TipoTarefa

# RN-21: os campos de cada tipo (texto igual ao de 03-dados). O `IS NOT NULL` da meta é
# necessário: `NULL BETWEEN 1 AND 31` dá NULL, e uma CHECK só rejeita FALSE.
TIPO_CAMPOS = (
    "(tipo = 'simples' AND recorrencia IS NULL AND meta_mensal IS NULL) OR "
    "(tipo = 'repetida' AND prazo IS NOT NULL AND recorrencia IS NOT NULL "
    "AND meta_mensal IS NULL) OR "
    "(tipo = 'meta_mensal' AND prazo IS NULL AND recorrencia IS NULL "
    "AND meta_mensal IS NOT NULL AND meta_mensal BETWEEN 1 AND 31)"
)


class Tarefa(Base):
    __tablename__ = "tarefas"
    __table_args__ = (
        CheckConstraint(TIPO_CAMPOS, name="tipo_campos"),
        Index("ix_tarefas_projeto_id_status_posicao", "projeto_id", "status", "posicao"),
        Index("ix_tarefas_prazo", "prazo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    projeto_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projetos.id", ondelete="CASCADE")
    )
    titulo: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str] = mapped_column(Text)
    status: Mapped[StatusTarefa] = mapped_column(enum_texto(StatusTarefa))
    prioridade: Mapped[Prioridade] = mapped_column(enum_texto(Prioridade))
    tipo: Mapped[TipoTarefa] = mapped_column(enum_texto(TipoTarefa))
    prazo: Mapped[date | None]
    # none_as_null: `None` vira NULL no banco (e não o JSON `null`), como o CHECK exige.
    recorrencia: Mapped[dict[str, Any] | None] = mapped_column(JSON(none_as_null=True))
    meta_mensal: Mapped[int | None]
    posicao: Mapped[int]
    concluida_em: Mapped[datetime | None] = mapped_column(UTCDateTime)
    busca: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    atualizado_em: Mapped[datetime] = mapped_column(UTCDateTime)
    excluido_em: Mapped[datetime | None] = mapped_column(UTCDateTime)


class TarefaExecucao(Base):
    """Conclusões de repetidas e execuções de metas (usadas nas fases 2.2 e 2.3)."""

    __tablename__ = "tarefa_execucoes"
    __table_args__ = (Index("ix_tarefa_execucoes_tarefa_id_data", "tarefa_id", "data"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tarefa_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tarefas.id", ondelete="CASCADE"))
    data: Mapped[date]
    prazo_referencia: Mapped[date | None]
    criado_em: Mapped[datetime] = mapped_column(UTCDateTime)
