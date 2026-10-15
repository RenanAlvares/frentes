from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.clock import Clock, ClockFixo

FUSO = ZoneInfo("America/Sao_Paulo")


def test_clock_agora_utc_tem_fuso_utc() -> None:
    assert Clock("America/Sao_Paulo").agora_utc().tzinfo is UTC


def test_rn01_clock_hoje_e_a_data_no_fuso_configurado() -> None:
    clock = Clock("America/Sao_Paulo")

    assert clock.hoje() in {
        clock.agora_utc().astimezone(FUSO).date(),
        datetime.now(FUSO).date(),  # caso vire a meia-noite entre as chamadas
    }


def test_rn01_clock_com_hoje_simulado() -> None:
    clock = Clock("America/Sao_Paulo", hoje_simulado=date(2026, 10, 31))

    assert clock.hoje() == date(2026, 10, 31)
    agora = clock.agora_utc()
    assert agora.tzinfo is UTC
    assert agora.astimezone(FUSO).date() == date(2026, 10, 31)


def test_clock_fixo_e_meio_dia_local_do_dia_definido() -> None:
    relogio = ClockFixo(date(2026, 10, 14))

    assert relogio.hoje() == date(2026, 10, 14)
    assert relogio.agora_utc() == datetime(2026, 10, 14, 15, 0, tzinfo=UTC)

    relogio.definir(date(2026, 10, 31))

    assert relogio.hoje() == date(2026, 10, 31)
    assert relogio.agora_utc().date() == date(2026, 10, 31)
