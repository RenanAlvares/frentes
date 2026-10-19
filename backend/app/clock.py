"""Relógio da aplicação: única fonte de "agora" e "hoje" (RN-01, 06 §7)."""

from datetime import UTC, date, datetime, time
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends

from app.config import Settings, get_settings


class Clock:
    def __init__(self, timezone: str, hoje_simulado: date | None = None) -> None:
        self._fuso = ZoneInfo(timezone)
        self._hoje_simulado = hoje_simulado

    def agora_utc(self) -> datetime:
        agora = datetime.now(self._fuso)
        if self._hoje_simulado is not None:
            # Data simulada com a hora real do dia no fuso configurado.
            agora = datetime.combine(self._hoje_simulado, agora.timetz())
        return agora.astimezone(UTC)

    def hoje(self) -> date:
        if self._hoje_simulado is not None:
            return self._hoje_simulado
        return datetime.now(self._fuso).date()

    def agora_local(self) -> datetime:
        """Agora no fuso configurado (nomes de arquivo de backup, RN-110/112)."""
        return self.agora_utc().astimezone(self._fuso)

    def data_local(self, momento: datetime) -> date:
        """A data de um carimbo UTC no fuso configurado (para contar dias contra `hoje`)."""
        return momento.astimezone(self._fuso).date()


class ClockFixo(Clock):
    """Relógio parado para testes: "agora" é meio-dia (no fuso) do dia definido."""

    def __init__(self, hoje: date, timezone: str = "America/Sao_Paulo") -> None:
        super().__init__(timezone)
        self._hoje = hoje

    def definir(self, hoje: date) -> None:
        self._hoje = hoje

    def agora_utc(self) -> datetime:
        return datetime.combine(self._hoje, time(12, 0), tzinfo=self._fuso).astimezone(UTC)

    def hoje(self) -> date:
        return self._hoje


def get_clock(settings: Annotated[Settings, Depends(get_settings)]) -> Clock:
    return Clock(settings.timezone, settings.hoje_simulado)
