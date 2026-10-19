"""Casos de uso de anotações (RN-80..81, RN-90)."""

import uuid

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.textos import normalizar_busca
from app.erros import NaoEncontrado
from app.models.anotacao import Anotacao as AnotacaoModelo
from app.repositories import anotacoes as repositorio
from app.repositories import projetos as repositorio_projetos
from app.schemas.anotacoes import Anotacao, AnotacaoAtualizar, AnotacaoCriar


def _resposta(anotacao: AnotacaoModelo) -> Anotacao:
    return Anotacao.model_validate(anotacao, from_attributes=True)


def _buscar_projeto(sessao: Session, projeto_id: uuid.UUID) -> None:
    if repositorio_projetos.obter(sessao, projeto_id) is None:
        raise NaoEncontrado("Projeto não encontrado.")


def _buscar(sessao: Session, anotacao_id: uuid.UUID) -> AnotacaoModelo:
    anotacao = repositorio.obter(sessao, anotacao_id)
    if anotacao is None:
        raise NaoEncontrado("Anotação não encontrada.")
    return anotacao


def listar_anotacoes(sessao: Session, projeto_id: uuid.UUID) -> list[Anotacao]:
    _buscar_projeto(sessao, projeto_id)
    return [_resposta(a) for a in repositorio.do_projeto(sessao, projeto_id)]


def criar_anotacao(
    sessao: Session, clock: Clock, projeto_id: uuid.UUID, dados: AnotacaoCriar
) -> Anotacao:
    _buscar_projeto(sessao, projeto_id)
    agora = clock.agora_utc()
    anotacao = AnotacaoModelo(
        projeto_id=projeto_id,
        **dados.model_dump(),
        busca=normalizar_busca(dados.titulo, dados.texto),
        criado_em=agora,
        atualizado_em=agora,
    )
    sessao.add(anotacao)
    sessao.commit()
    return _resposta(anotacao)


def atualizar_anotacao(
    sessao: Session, clock: Clock, anotacao_id: uuid.UUID, dados: AnotacaoAtualizar
) -> Anotacao:
    anotacao = _buscar(sessao, anotacao_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(anotacao, campo, valor)
    anotacao.busca = normalizar_busca(anotacao.titulo, anotacao.texto)
    # Toda alteração conta para RN-81, inclusive fixar/desafixar.
    anotacao.atualizado_em = clock.agora_utc()
    sessao.commit()
    return _resposta(anotacao)


def excluir_anotacao(sessao: Session, clock: Clock, anotacao_id: uuid.UUID) -> None:
    # RN-90: exclusão lógica; vai para a lixeira.
    anotacao = _buscar(sessao, anotacao_id)
    anotacao.excluido_em = clock.agora_utc()
    sessao.commit()
