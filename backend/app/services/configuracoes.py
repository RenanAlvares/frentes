"""Casos de uso das configurações (RN-100)."""

from sqlalchemy.orm import Session

from app.clock import Clock
from app.models.configuracao import Configuracao
from app.repositories import configuracoes as repositorio

PADROES: dict[str, int] = {
    "aviso_tarefas_dias": 3,
    "antecedencia_padrao_lembretes": 3,
}


def criar_padroes_faltantes(sessao: Session, clock: Clock) -> None:
    """RN-100: cria com o valor padrão as chaves que ainda não existem (não altera as demais)."""
    existentes = repositorio.chaves_existentes(sessao)
    agora = clock.agora_utc()
    sessao.add_all(
        Configuracao(chave=chave, valor=valor, atualizado_em=agora)
        for chave, valor in PADROES.items()
        if chave not in existentes
    )
    sessao.commit()
