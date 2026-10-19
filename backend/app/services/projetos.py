"""Casos de uso de projetos (RN-10..17, RN-90)."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.textos import normalizar_busca
from app.erros import NaoEncontrado, Validacao
from app.models.projeto import Projeto as ProjetoModelo
from app.repositories import projetos as repositorio
from app.repositories import tarefas as repositorio_tarefas
from app.schemas.projetos import (
    Progresso,
    Projeto,
    ProjetoAtualizar,
    ProjetoCriar,
    ProjetoResumo,
    ProjetosOrdem,
)
from app.services import avisos as servico_avisos


def _progressos(
    sessao: Session, projetos: list[ProjetoModelo]
) -> dict[uuid.UUID, Progresso | None]:
    """RN-13: só para quem acompanha o progresso; uma consulta para todos."""
    contagens = repositorio_tarefas.progresso_por_projeto(
        sessao, [projeto.id for projeto in projetos if projeto.acompanhar_progresso]
    )
    progressos: dict[uuid.UUID, Progresso | None] = {}
    for projeto in projetos:
        concluidas, total = contagens.get(projeto.id, (0, 0))
        acompanha = projeto.acompanhar_progresso
        progressos[projeto.id] = (
            Progresso(concluidas=concluidas, total=total) if acompanha else None
        )
    return progressos


def _campos(projeto: ProjetoModelo, progresso: Progresso | None, avisos: int) -> dict[str, object]:
    """Colunas do modelo + campos calculados da resposta (RN-13, RN-57)."""
    colunas = {coluna.key: getattr(projeto, coluna.key) for coluna in projeto.__table__.columns}
    return {**colunas, "progresso": progresso, "avisos": avisos}


def _resumos(sessao: Session, hoje: date, projetos: list[ProjetoModelo]) -> list[ProjetoResumo]:
    progressos = _progressos(sessao, projetos)
    avisos = servico_avisos.contar_por_projeto(sessao, hoje, projetos)
    return [
        ProjetoResumo.model_validate(_campos(p, progressos[p.id], avisos[p.id])) for p in projetos
    ]


def _detalhe(sessao: Session, hoje: date, projeto: ProjetoModelo) -> Projeto:
    progresso = _progressos(sessao, [projeto])[projeto.id]
    avisos = servico_avisos.contar_por_projeto(sessao, hoje, [projeto])[projeto.id]
    return Projeto.model_validate(_campos(projeto, progresso, avisos))


def _validar_datas(data_inicio: date | None, prazo: date | None) -> None:
    # RN-16
    if data_inicio is not None and prazo is not None and data_inicio > prazo:
        raise Validacao(campos={"prazo": "O prazo não pode ser anterior ao início."})


def _buscar(sessao: Session, projeto_id: uuid.UUID) -> ProjetoModelo:
    projeto = repositorio.obter(sessao, projeto_id)
    if projeto is None:
        raise NaoEncontrado("Projeto não encontrado.")
    return projeto


def listar_projetos(sessao: Session, clock: Clock, *, arquivados: bool) -> list[ProjetoResumo]:
    return _resumos(sessao, clock.hoje(), repositorio.listar(sessao, arquivados=arquivados))


def obter_projeto(sessao: Session, clock: Clock, projeto_id: uuid.UUID) -> Projeto:
    return _detalhe(sessao, clock.hoje(), _buscar(sessao, projeto_id))


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
    return _detalhe(sessao, clock.hoje(), projeto)


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
    return _detalhe(sessao, clock.hoje(), projeto)


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
