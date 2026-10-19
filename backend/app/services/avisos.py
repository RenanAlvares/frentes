"""Avisos (RN-50..58): junta os candidatos do banco e aplica `domain/avisos.py`."""

import uuid
from collections import Counter
from dataclasses import asdict
from datetime import date

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain import avisos as dominio
from app.domain.enums import StatusProjeto, TipoTarefa
from app.domain.metas import mes_de
from app.domain.recorrencia import Recorrencia
from app.models.projeto import Projeto
from app.repositories import configuracoes as repositorio_configuracoes
from app.repositories import lembretes as repositorio_lembretes
from app.repositories import projetos as repositorio_projetos
from app.repositories import tarefas as repositorio_tarefas
from app.schemas.avisos import Avisos
from app.services.configuracoes import PADROES

AVISO_TAREFAS_DIAS = "aviso_tarefas_dias"


def _aviso_tarefas_dias(sessao: Session) -> int:
    valor = repositorio_configuracoes.valor(sessao, AVISO_TAREFAS_DIAS)
    return valor if isinstance(valor, int) else PADROES[AVISO_TAREFAS_DIAS]


def calcular(sessao: Session, hoje: date, projetos: list[Projeto]) -> list[dominio.Aviso]:
    """RN-50: só projetos ativos (os excluídos nem chegam aqui) e itens não excluídos."""
    ativos = {
        p.id: dominio.ProjetoDoAviso(id=p.id, nome=p.nome, cor=p.cor)
        for p in projetos
        if p.status != StatusProjeto.CONCLUIDO
    }
    ids = list(ativos)
    lembretes = [
        dominio.LembreteCandidato(
            id=lb.id,
            titulo=lb.titulo,
            projeto=ativos[lb.projeto_id],
            vencimento=lb.vencimento,
            antecedencia_dias=lb.antecedencia_dias,
            recorrencia=Recorrencia.model_validate(lb.recorrencia) if lb.recorrencia else None,
        )
        for lb in repositorio_lembretes.ativos_dos_projetos(sessao, ids)
    ]
    tarefas = repositorio_tarefas.nao_concluidas_dos_projetos(sessao, ids)
    metas = [t.id for t in tarefas if t.tipo == TipoTarefa.META_MENSAL]
    do_mes = repositorio_tarefas.execucoes_no_periodo(sessao, metas, *mes_de(hoje))
    candidatas = [
        dominio.TarefaCandidata(
            id=t.id,
            titulo=t.titulo,
            projeto=ativos[t.projeto_id],
            tipo=t.tipo,
            prazo=t.prazo,
            meta_mensal=t.meta_mensal,
            progresso_mes=len(do_mes.get(t.id, [])),
        )
        for t in tarefas
    ]
    return dominio.calcular_avisos(lembretes, candidatas, hoje, _aviso_tarefas_dias(sessao))


def contar_por_projeto(sessao: Session, hoje: date, projetos: list[Projeto]) -> Counter[uuid.UUID]:
    """RN-57: quantidade de avisos de cada projeto (mesmas regras do painel)."""
    return Counter(aviso.projeto.id for aviso in calcular(sessao, hoje, projetos))


def listar_avisos(sessao: Session, clock: Clock) -> Avisos:
    itens = calcular(sessao, clock.hoje(), repositorio_projetos.listar(sessao, arquivados=False))
    return Avisos.model_validate({"total": len(itens), "itens": [asdict(a) for a in itens]})
