from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.dialects import sqlite

from app.db.base import NAMING, Base
from app.db.tipos import UTCDateTime

DIALETO = sqlite.dialect()
TIPO = UTCDateTime()


def test_rn02_grava_em_utc_sem_fuso() -> None:
    em_sao_paulo = datetime(2026, 10, 14, 19, 30, tzinfo=timezone(timedelta(hours=-3)))

    gravado = TIPO.process_bind_param(em_sao_paulo, DIALETO)

    assert gravado == datetime(2026, 10, 14, 22, 30, tzinfo=UTC).replace(tzinfo=None)


def test_rn02_recusa_datetime_sem_fuso() -> None:
    with pytest.raises(ValueError, match="fuso"):
        TIPO.process_bind_param(datetime(2026, 10, 14, 22, 30), DIALETO)  # noqa: DTZ001


def test_rn02_devolve_com_tzinfo_utc() -> None:
    lido = TIPO.process_result_value(datetime(2026, 10, 14, 22, 30), DIALETO)  # noqa: DTZ001

    assert lido == datetime(2026, 10, 14, 22, 30, tzinfo=UTC)
    assert lido is not None
    assert lido.tzinfo is UTC


def test_rn02_converte_para_utc_valor_lido_com_fuso() -> None:
    lido = TIPO.process_result_value(
        datetime(2026, 10, 14, 19, 30, tzinfo=timezone(timedelta(hours=-3))), DIALETO
    )

    assert lido == datetime(2026, 10, 14, 22, 30, tzinfo=UTC)
    assert lido is not None
    assert lido.tzinfo is UTC


def test_nulos_passam_direto() -> None:
    assert TIPO.process_bind_param(None, DIALETO) is None
    assert TIPO.process_result_value(None, DIALETO) is None


def test_base_usa_naming_convention() -> None:
    assert NAMING.items() <= Base.metadata.naming_convention.items()
