"""Lixeira (04-api, Lixeira)."""

from enum import StrEnum


class TipoItemLixeira(StrEnum):
    # Documento e anotação entram com as fases 4 e 5.1.
    PROJETO = "projeto"
    TAREFA = "tarefa"
    LEMBRETE = "lembrete"
