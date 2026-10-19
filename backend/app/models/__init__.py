"""Importa todos os modelos para registrá-los no `Base.metadata` (usado pelo Alembic)."""

from app.models.anotacao import Anotacao
from app.models.configuracao import Configuracao
from app.models.documento import Documento
from app.models.lembrete import Lembrete, LembreteBaixa
from app.models.projeto import Projeto
from app.models.tarefa import Tarefa, TarefaExecucao

__all__ = [
    "Anotacao",
    "Configuracao",
    "Documento",
    "Lembrete",
    "LembreteBaixa",
    "Projeto",
    "Tarefa",
    "TarefaExecucao",
]
