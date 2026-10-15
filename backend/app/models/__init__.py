"""Importa todos os modelos para registrá-los no `Base.metadata` (usado pelo Alembic)."""

from app.models.configuracao import Configuracao

__all__ = ["Configuracao"]
