"""Metas mensais (RN-24). Funções puras: recebem `hoje` e as execuções, sem banco e sem relógio."""

import calendar
from dataclasses import dataclass
from datetime import date, datetime


def mes_de(hoje: date) -> tuple[date, date]:
    """Primeiro e último dia do mês de `hoje` (contagem por intervalo de datas, 03-dados)."""
    return hoje.replace(day=1), hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])


@dataclass(frozen=True)
class SituacaoMeta:
    progresso: int
    """Execuções no mês de hoje (`progresso_mes`)."""
    atingida_em: datetime | None
    """Quando a meta foi atingida no mês: o registro da execução que completou a meta."""


def situacao_meta(meta: int, registros_do_mes: list[datetime]) -> SituacaoMeta:
    """RN-24: progresso do mês; a coluna derivada é Concluída quando `progresso ≥ meta`.

    Execuções além da meta não mudam `atingida_em` (a posição na coluna Concluída).
    """
    ordenados = sorted(registros_do_mes)
    atingida = ordenados[meta - 1] if len(ordenados) >= meta else None
    return SituacaoMeta(progresso=len(ordenados), atingida_em=atingida)
