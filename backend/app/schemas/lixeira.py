"""Lixeira (04-api, Lixeira)."""

from enum import StrEnum


class TipoItemLixeira(StrEnum):
    # Anotação entra com a 4.3.
    PROJETO = "projeto"
    TAREFA = "tarefa"
    LEMBRETE = "lembrete"
    DOCUMENTO = "documento"
