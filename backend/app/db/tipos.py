"""Tipos de coluna próprios (03-dados, convenções)."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, Dialect, Enum
from sqlalchemy.types import TypeDecorator


def enum_texto(classe: type[StrEnum]) -> Enum:
    """Enum como VARCHAR(20) + CHECK, igual em SQLite e PostgreSQL (03-dados, convenções)."""
    return Enum(
        classe,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda membros: [membro.value for membro in membros],
    )


class UTCDateTime(TypeDecorator[datetime]):
    """Grava em UTC sem fuso e devolve `datetime` com `tzinfo=UTC` (RN-02)."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.utcoffset() is None:
            raise ValueError("UTCDateTime exige datetime com fuso horário.")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
