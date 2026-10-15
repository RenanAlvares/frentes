"""Lixeira (04-api, Lixeira)."""

from enum import StrEnum


class TipoItemLixeira(StrEnum):
    # Os demais tipos (tarefa, lembrete, documento, anotacao) entram na fase 5.1.
    PROJETO = "projeto"
