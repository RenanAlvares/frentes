"""Lixeira (04-api, Lixeira)."""

from enum import StrEnum


class TipoItemLixeira(StrEnum):
    PROJETO = "projeto"
    TAREFA = "tarefa"
    LEMBRETE = "lembrete"
    DOCUMENTO = "documento"
    ANOTACAO = "anotacao"
