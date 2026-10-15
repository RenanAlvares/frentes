"""Configuração do app: variáveis de ambiente com prefixo FRENTES_ (06 §6)."""

from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Request
from platformdirs import user_data_dir
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FRENTES_",
        env_file=RAIZ_REPOSITORIO / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Path(user_data_dir("Frentes"))
    # Vazio = sqlite:///{data_dir}/frentes.db
    database_url: str = ""
    timezone: str = "America/Sao_Paulo"
    host: str = "127.0.0.1"
    port: int = 8765
    max_upload_mb: int = 50
    lixeira_dias: int = 30
    abrir_navegador: bool = True
    # Só para teste manual: data que o Clock usa como "hoje".
    hoje_simulado: date | None = None

    @field_validator("hoje_simulado", mode="before")
    @classmethod
    def _vazio_vira_none(cls, valor: object) -> object:
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    @field_validator("timezone")
    @classmethod
    def _fuso_existe(cls, valor: str) -> str:
        try:
            ZoneInfo(valor)
        except (ZoneInfoNotFoundError, ValueError) as erro:
            raise ValueError(f"Fuso horário desconhecido: {valor!r}.") from erro
        return valor

    @model_validator(mode="after")
    def _resolver_caminhos(self) -> "Settings":
        if not self.data_dir.is_absolute():
            self.data_dir = RAIZ_REPOSITORIO / self.data_dir
        if not self.database_url:
            self.database_url = f"sqlite:///{(self.data_dir / 'frentes.db').as_posix()}"
        return self

    @property
    def pasta_anexos(self) -> Path:
        return self.data_dir / "anexos"

    @property
    def pasta_backups(self) -> Path:
        return self.data_dir / "backups"


def get_settings(request: Request) -> Settings:
    """Dependência: o Settings com que o app foi criado."""
    settings: Settings = request.app.state.settings
    return settings
