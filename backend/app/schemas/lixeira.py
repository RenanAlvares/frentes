"""Lixeira (04-api, Lixeira)."""

from enum import StrEnum


class TipoItemLixeira(StrEnum):
    # Lembrete, documento e anotação entram com as fases 3, 4 e 5.1.
    PROJETO = "projeto"
    TAREFA = "tarefa"
