"""Casos de uso de projetos (RN-10..17, RN-90)."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.textos import normalizar_busca
from app.erros import NaoEncontrado, Validacao
from app.models.projeto import Projeto as ProjetoModelo
from app.repositories import projetos as repositorio
from app.schemas.projetos import (
    Progresso,
    Projeto,
    ProjetoAtualizar,
    ProjetoCriar,
    ProjetoResumo,
    ProjetosOrdem,
)


def _campos(projeto: ProjetoModelo) -> dict[str, object]:
    """Colunas do modelo + campos calculados da resposta."""
    colunas = {coluna.key: getattr(projeto, coluna.key) for coluna in projeto.__table__.columns}
    # RN-13 conta tarefas simples (tarefas entram na 1.4/1.7); avisos entram na fase 3.
    progresso = Progresso(concluidas=0, total=0) if projeto.acompanhar_progresso else None
    return {**colunas, "progresso": progresso, "avisos": 0}


def _resumo(projeto: ProjetoModelo) -> ProjetoResumo:
    return ProjetoResumo.model_validate(_campos(projeto))


def _detalhe(projeto: ProjetoModelo) -> Projeto:
    return Projeto.model_validate(_campos(projeto))


def _validar_datas(data_inicio: date | None, prazo: date | None) -> None:
    # RN-16
    if data_inicio is not None and prazo is not None and data_inicio > prazo:
        raise Validacao(campos={"prazo": "O prazo não pode ser anterior ao início."})


def _buscar(sessao: Session, projeto_id: uuid.UUID) -> ProjetoModelo:
    projeto = repositorio.obter(sessao, projeto_id)
    if projeto is None:
        raise NaoEncontrado("Projeto não encontrado.")
    return projeto


def listar_projetos(sessao: Session, *, arquivados: bool) -> list[ProjetoResumo]:
    return [_resumo(projeto) for projeto in repositorio.listar(sessao, arquivados=arquivados)]


def obter_projeto(sessao: Session, projeto_id: uuid.UUID) -> Projeto:
    return _detalhe(_buscar(sessao, projeto_id))


def criar_projeto(sessao: Session, clock: Clock, dados: ProjetoCriar) -> Projeto:
    _validar_datas(dados.data_inicio, dados.prazo)
    agora = clock.agora_utc()
    projeto = ProjetoModelo(
        **dados.model_dump(),
        posicao=repositorio.proxima_posicao(sessao),
        busca=normalizar_busca(dados.nome, dados.descricao),
        criado_em=agora,
        atualizado_em=agora,
    )
    sessao.add(projeto)
    sessao.commit()
    return _detalhe(projeto)


def atualizar_projeto(
    sessao: Session, clock: Clock, projeto_id: uuid.UUID, dados: ProjetoAtualizar
) -> Projeto:
    projeto = _buscar(sessao, projeto_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    _validar_datas(
        alteracoes.get("data_inicio", projeto.data_inicio), alteracoes.get("prazo", projeto.prazo)
    )
    for campo, valor in alteracoes.items():
        setattr(projeto, campo, valor)
    projeto.busca = normalizar_busca(projeto.nome, projeto.descricao)
    projeto.atualizado_em = clock.agora_utc()
    sessao.commit()
    return _detalhe(projeto)


def excluir_projeto(sessao: Session, clock: Clock, projeto_id: uuid.UUID) -> None:
    # RN-90: exclusão lógica; vai para a lixeira.
    projeto = _buscar(sessao, projeto_id)
    projeto.excluido_em = clock.agora_utc()
    sessao.commit()


def reordenar_projetos(sessao: Session, dados: ProjetosOrdem) -> None:
    # RN-15: a lista tem de ter exatamente os projetos ativos, sem repetição.
    ativos = {projeto.id: projeto for projeto in repositorio.listar(sessao, arquivados=False)}
    if len(dados.ids) != len(ativos) or set(dados.ids) != set(ativos):
        raise Validacao(campos={"ids": "Envie todos os projetos ativos, cada um uma vez."})
    for posicao, projeto_id in enumerate(dados.ids):
        ativos[projeto_id].posicao = posicao
    sessao.commit()
