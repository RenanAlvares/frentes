"""Metas mensais (RN-24): funções puras."""

from datetime import UTC, date, datetime

import pytest

from app.domain.metas import SituacaoMeta, mes_de, situacao_meta


@pytest.mark.parametrize(
    ("hoje", "esperado"),
    [
        (date(2026, 10, 14), (date(2026, 10, 1), date(2026, 10, 31))),
        (date(2028, 2, 29), (date(2028, 2, 1), date(2028, 2, 29))),
        (date(2027, 2, 1), (date(2027, 2, 1), date(2027, 2, 28))),
        (date(2026, 12, 31), (date(2026, 12, 1), date(2026, 12, 31))),
    ],
)
def test_rn24_mes_de(hoje: date, esperado: tuple[date, date]) -> None:
    assert mes_de(hoje) == esperado


def _as(*horas: int) -> list[datetime]:
    return [datetime(2026, 10, 14, hora, tzinfo=UTC) for hora in horas]


@pytest.mark.parametrize(
    ("meta", "registros", "esperado"),
    [
        (4, _as(), SituacaoMeta(0, None)),
        (4, _as(9, 10, 11), SituacaoMeta(3, None)),
        # A 4ª execução registrada completa a meta.
        (4, _as(12, 9, 11, 10), SituacaoMeta(4, _as(12)[0])),
        # Passar da meta (5/4) não muda quando ela foi atingida.
        (4, _as(9, 10, 11, 12, 13), SituacaoMeta(5, _as(12)[0])),
        (1, _as(15), SituacaoMeta(1, _as(15)[0])),
    ],
)
def test_rn24_situacao_meta(meta: int, registros: list[datetime], esperado: SituacaoMeta) -> None:
    assert situacao_meta(meta, registros) == esperado
