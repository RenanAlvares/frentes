from datetime import date
from typing import Literal

from pydantic import BaseModel


class SaudeResposta(BaseModel):
    status: Literal["ok"]
    versao: str
    hoje: date
    hoje_simulado: bool
