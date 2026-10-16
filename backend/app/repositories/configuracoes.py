"""Consultas da tabela `configuracoes`."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.configuracao import Configuracao


def chaves_existentes(sessao: Session) -> set[str]:
    return set(sessao.scalars(select(Configuracao.chave)))


def valor(sessao: Session, chave: str) -> object | None:
    return sessao.scalar(select(Configuracao.valor).where(Configuracao.chave == chave))
