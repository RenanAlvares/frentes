"""Importa todos os modelos para registrá-los no `Base.metadata` (usado pelo Alembic)."""

from app.models.configuracao import Configuracao
from app.models.projeto import Projeto

__all__ = ["Configuracao", "Projeto"]
