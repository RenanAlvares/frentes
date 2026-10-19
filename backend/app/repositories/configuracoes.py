"""Consultas da tabela `configuracoes`."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.configuracao import Configuracao


def chaves_existentes(sessao: Session) -> set[str]:
    return set(sessao.scalars(select(Configuracao.chave)))


def todas(sessao: Session) -> dict[str, Any]:
    return {c.chave: c.valor for c in sessao.scalars(select(Configuracao))}


def gravar(sessao: Session, chave: str, valor: Any, agora: datetime) -> None:
    configuracao = sessao.get(Configuracao, chave)
    if configuracao is None:
        sessao.add(Configuracao(chave=chave, valor=valor, atualizado_em=agora))
    else:
        configuracao.valor = valor
        configuracao.atualizado_em = agora
