"""Casos de uso das configurações (RN-100)."""

from sqlalchemy.orm import Session

from app.clock import Clock
from app.models.configuracao import Configuracao
from app.repositories import configuracoes as repositorio
from app.schemas.configuracoes import Configuracoes, ConfiguracoesAtualizar

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


def _inteiro(valor: object, padrao: int) -> int:
    # A coluna é JSON (03-dados): um valor fora do formato não derruba a tela, vale o padrão.
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else padrao


def obter_configuracoes(sessao: Session) -> Configuracoes:
    """Única leitura das configurações (avisos e lembretes usam esta também)."""
    gravadas = repositorio.todas(sessao)
    return Configuracoes.model_validate(
        {chave: _inteiro(gravadas.get(chave), padrao) for chave, padrao in PADROES.items()}
    )


def atualizar_configuracoes(
    sessao: Session, clock: Clock, dados: ConfiguracoesAtualizar
) -> Configuracoes:
    agora = clock.agora_utc()
    for chave, valor in dados.model_dump(exclude_unset=True).items():
        repositorio.gravar(sessao, chave, valor, agora)
    sessao.commit()
    return obter_configuracoes(sessao)
