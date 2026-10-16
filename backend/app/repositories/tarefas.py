"""Consultas de tarefas. Excluídas (RN-90) e as de projeto excluído (RN-91) ficam de fora."""

import uuid

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.domain.enums import StatusTarefa, TipoTarefa
from app.models.projeto import Projeto
from app.models.tarefa import Tarefa, TarefaExecucao

_VISIVEL = (Tarefa.excluido_em.is_(None), Projeto.excluido_em.is_(None))


def _visiveis() -> Select[Tarefa]:
    return select(Tarefa).join(Projeto, Tarefa.projeto_id == Projeto.id).where(*_VISIVEL)


def _do_projeto(projeto_id: uuid.UUID) -> Select[Tarefa]:
    return _visiveis().where(Tarefa.projeto_id == projeto_id)


def obter(sessao: Session, tarefa_id: uuid.UUID) -> Tarefa | None:
    return sessao.scalar(_visiveis().where(Tarefa.id == tarefa_id))


def obter_excluida(sessao: Session, tarefa_id: uuid.UUID) -> Tarefa | None:
    """Só para a Lixeira: excluída, com o projeto fora da lixeira (RN-91)."""
    consulta = (
        select(Tarefa)
        .join(Projeto, Tarefa.projeto_id == Projeto.id)
        .where(
            Tarefa.id == tarefa_id,
            Tarefa.excluido_em.is_not(None),
            Projeto.excluido_em.is_(None),
        )
    )
    return sessao.scalar(consulta)


def da_coluna(sessao: Session, projeto_id: uuid.UUID, status: StatusTarefa) -> list[Tarefa]:
    """Pendente e Em andamento: `posicao` crescente (RN-25)."""
    consulta = (
        _do_projeto(projeto_id)
        .where(Tarefa.status == status)
        .order_by(Tarefa.posicao, Tarefa.criado_em)
    )
    return list(sessao.scalars(consulta))


def concluidas(sessao: Session, projeto_id: uuid.UUID, limite: int | None = None) -> list[Tarefa]:
    """Concluída: `concluida_em` decrescente (RN-25)."""
    consulta = (
        _do_projeto(projeto_id)
        .where(Tarefa.status == StatusTarefa.CONCLUIDA)
        .order_by(Tarefa.concluida_em.desc(), Tarefa.criado_em.desc())
        .limit(limite)
    )
    return list(sessao.scalars(consulta))


def progresso_por_projeto(
    sessao: Session, projeto_ids: list[uuid.UUID]
) -> dict[uuid.UUID, tuple[int, int]]:
    """RN-13: (concluídas, total) das tarefas simples não excluídas de cada projeto."""
    if not projeto_ids:
        return {}
    concluida = case((Tarefa.status == StatusTarefa.CONCLUIDA, 1), else_=0)
    consulta = (
        select(Tarefa.projeto_id, func.sum(concluida), func.count())
        .where(
            Tarefa.projeto_id.in_(projeto_ids),
            Tarefa.tipo == TipoTarefa.SIMPLES,
            Tarefa.excluido_em.is_(None),
        )
        .group_by(Tarefa.projeto_id)
    )
    return {
        projeto_id: (int(feitas), total) for projeto_id, feitas, total in sessao.execute(consulta)
    }


def execucoes(sessao: Session, tarefa_id: uuid.UUID, limite: int) -> list[TarefaExecucao]:
    """Mais recentes primeiro (`criado_em` desempata no mesmo dia, 03-dados)."""
    consulta = (
        select(TarefaExecucao)
        .where(TarefaExecucao.tarefa_id == tarefa_id)
        .order_by(TarefaExecucao.data.desc(), TarefaExecucao.criado_em.desc())
        .limit(limite)
    )
    return list(sessao.scalars(consulta))


def contar_concluidas(sessao: Session, projeto_id: uuid.UUID) -> int:
    consulta = (
        select(func.count())
        .select_from(Tarefa)
        .join(Projeto, Tarefa.projeto_id == Projeto.id)
        .where(Tarefa.projeto_id == projeto_id, Tarefa.status == StatusTarefa.CONCLUIDA, *_VISIVEL)
    )
    return sessao.scalar(consulta) or 0
