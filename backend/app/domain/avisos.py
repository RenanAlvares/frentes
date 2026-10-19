"""Avisos (RN-50..58). Puro: recebe os itens candidatos e `hoje`; devolve a lista ordenada."""

import uuid
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from app.domain.enums import TipoTarefa
from app.domain.metas import mes_de
from app.domain.recorrencia import Recorrencia, ocorrencias_atrasadas


@dataclass(frozen=True)
class ProjetoDoAviso:
    id: uuid.UUID
    nome: str
    cor: str


@dataclass(frozen=True)
class LembreteCandidato:
    """Lembrete ativo (RN-41): sem baixa definitiva, não excluído, de projeto ativo."""

    id: uuid.UUID
    titulo: str
    projeto: ProjetoDoAviso
    vencimento: date
    antecedencia_dias: int
    recorrencia: Recorrencia | None


@dataclass(frozen=True)
class TarefaCandidata:
    """Tarefa não concluída e não excluída, de projeto ativo. Metas trazem o progresso do mês."""

    id: uuid.UUID
    titulo: str
    projeto: ProjetoDoAviso
    tipo: TipoTarefa
    prazo: date | None
    meta_mensal: int | None = None
    progresso_mes: int = 0


@dataclass(frozen=True)
class MetaDoAviso:
    feitas: int
    meta: int


@dataclass(frozen=True)
class Aviso:
    """RN-56."""

    tipo: Literal["lembrete", "tarefa"]
    id: uuid.UUID
    titulo: str
    projeto: ProjetoDoAviso
    vencimento: date
    dias_restantes: int
    ocorrencias_atrasadas: int
    meta: MetaDoAviso | None


def na_janela(vencimento: date, antecedencia_dias: int, hoje: date) -> bool:
    """RN-42: a partir de `vencimento - antecedência` e até a baixa (inclusive vencido)."""
    return hoje >= vencimento - timedelta(days=antecedencia_dias)


def atrasadas_do_lembrete(recorrencia: Recorrencia | None, vencimento: date, hoje: date) -> int:
    """RN-34 para recorrentes; não recorrente conta 1 a partir do vencimento."""
    if recorrencia is not None:
        return ocorrencias_atrasadas(recorrencia, vencimento, hoje)
    return 1 if vencimento <= hoje else 0


def _de_lembretes(lembretes: Iterable[LembreteCandidato], hoje: date) -> Iterator[Aviso]:
    for lembrete in lembretes:
        if not na_janela(lembrete.vencimento, lembrete.antecedencia_dias, hoje):
            continue
        yield Aviso(
            tipo="lembrete",
            id=lembrete.id,
            titulo=lembrete.titulo,
            projeto=lembrete.projeto,
            vencimento=lembrete.vencimento,
            dias_restantes=(lembrete.vencimento - hoje).days,
            ocorrencias_atrasadas=atrasadas_do_lembrete(
                lembrete.recorrencia, lembrete.vencimento, hoje
            ),
            meta=None,
        )


def _de_tarefas(tarefas: Iterable[TarefaCandidata], hoje: date, dias: int) -> Iterator[Aviso]:
    _, ultimo_dia = mes_de(hoje)
    for tarefa in tarefas:
        meta: MetaDoAviso | None = None
        if tarefa.tipo == TipoTarefa.META_MENSAL:
            # RN-50.3: meta que ainda não foi atingida, perto do fim do mês.
            alvo = tarefa.meta_mensal or 1
            if tarefa.progresso_mes >= alvo:
                continue
            vencimento = ultimo_dia
            meta = MetaDoAviso(feitas=tarefa.progresso_mes, meta=alvo)
        elif tarefa.prazo is None:
            continue
        else:
            # RN-50.2: simples e repetidas com prazo.
            vencimento = tarefa.prazo
        if hoje < vencimento - timedelta(days=dias):
            continue
        yield Aviso(
            tipo="tarefa",
            id=tarefa.id,
            titulo=tarefa.titulo,
            projeto=tarefa.projeto,
            vencimento=vencimento,
            dias_restantes=(vencimento - hoje).days,
            ocorrencias_atrasadas=0,
            meta=meta,
        )


def calcular_avisos(
    lembretes: Iterable[LembreteCandidato],
    tarefas: Iterable[TarefaCandidata],
    hoje: date,
    aviso_tarefas_dias: int,
) -> list[Aviso]:
    """RN-50 e RN-51: mais atrasado primeiro; empate, lembrete antes de tarefa; depois o título."""
    avisos = [*_de_lembretes(lembretes, hoje), *_de_tarefas(tarefas, hoje, aviso_tarefas_dias)]
    return sorted(
        avisos, key=lambda a: (a.dias_restantes, a.tipo != "lembrete", a.titulo.casefold())
    )
