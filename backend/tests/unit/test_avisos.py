"""Avisos (RN-50..58): função pura. Casos de 07 §3.2, hoje = 2026-10-14."""

import uuid
from collections.abc import Sequence
from datetime import date

import pytest

from app.domain.avisos import (
    LembreteCandidato,
    MetaDoAviso,
    ProjetoDoAviso,
    TarefaCandidata,
    calcular_avisos,
)
from app.domain.enums import TipoTarefa
from app.domain.recorrencia import Recorrencia

HOJE = date(2026, 10, 14)
PROJETO = ProjetoDoAviso(id=uuid.uuid4(), nome="Casa", cor="azul")


def lembrete(
    vencimento: date,
    antecedencia: int = 3,
    titulo: str = "L",
    recorrencia: Recorrencia | None = None,
) -> LembreteCandidato:
    return LembreteCandidato(uuid.uuid4(), titulo, PROJETO, vencimento, antecedencia, recorrencia)


def tarefa(
    prazo: date | None, titulo: str = "T", tipo: TipoTarefa = TipoTarefa.SIMPLES
) -> TarefaCandidata:
    return TarefaCandidata(uuid.uuid4(), titulo, PROJETO, tipo, prazo)


def meta(feitas: int, alvo: int = 4, titulo: str = "M") -> TarefaCandidata:
    return TarefaCandidata(
        uuid.uuid4(),
        titulo,
        PROJETO,
        TipoTarefa.META_MENSAL,
        None,
        meta_mensal=alvo,
        progresso_mes=feitas,
    )


def avisos(
    lembretes: Sequence[LembreteCandidato] = (),
    tarefas: Sequence[TarefaCandidata] = (),
    hoje: date = HOJE,
    dias: int = 3,
) -> list[tuple[str, int]]:
    return [(a.titulo, a.dias_restantes) for a in calcular_avisos(lembretes, tarefas, hoje, dias)]


# Lembretes (RN-42)


@pytest.mark.parametrize(
    ("vencimento", "antecedencia", "esperado"),
    [
        (date(2026, 10, 17), 3, [("L", 3)]),  # primeiro dia da janela
        (date(2026, 10, 18), 3, []),
        (date(2026, 10, 14), 0, [("L", 0)]),
        (date(2026, 10, 11), 3, [("L", -3)]),  # vencido continua até a baixa
    ],
)
def test_rn42_janela_do_lembrete(
    vencimento: date, antecedencia: int, esperado: list[tuple[str, int]]
) -> None:
    assert avisos(lembretes=[lembrete(vencimento, antecedencia)]) == esperado


def test_rn34_rn56_ocorrencias_atrasadas_do_lembrete() -> None:
    mensal = Recorrencia(frequencia="mensal", dia_mes=5)
    candidatos = [
        lembrete(date(2026, 8, 5), titulo="Recorrente", recorrencia=mensal),
        lembrete(date(2026, 10, 11), titulo="Vencido"),
        lembrete(date(2026, 10, 16), titulo="Futuro"),
    ]

    resultado = {
        a.titulo: a.ocorrencias_atrasadas for a in calcular_avisos(candidatos, [], HOJE, 3)
    }

    assert resultado == {"Recorrente": 3, "Vencido": 1, "Futuro": 0}


# Tarefas (RN-50.2)


def test_rn50_tarefa_com_prazo_dentro_do_aviso() -> None:
    candidatas = [
        tarefa(date(2026, 10, 17), titulo="Dentro"),
        tarefa(date(2026, 10, 18), titulo="Fora"),
        tarefa(date(2026, 10, 1), titulo="Atrasada", tipo=TipoTarefa.REPETIDA),
        tarefa(None, titulo="Sem prazo"),
    ]

    assert avisos(tarefas=candidatas) == [("Atrasada", -13), ("Dentro", 3)]


def test_rn50_aviso_tarefas_dias_zero_tira_a_tarefa_de_17_10() -> None:
    assert avisos(tarefas=[tarefa(date(2026, 10, 17))], dias=0) == []
    assert avisos(tarefas=[tarefa(date(2026, 10, 14))], dias=0) == [("T", 0)]


# Metas (RN-50.3)


def test_rn50_meta_perto_do_fim_do_mes() -> None:
    assert avisos(tarefas=[meta(2)]) == []

    (aviso,) = calcular_avisos([], [meta(2)], date(2026, 10, 29), 3)

    assert aviso.dias_restantes == 2
    assert aviso.vencimento == date(2026, 10, 31)
    assert aviso.meta == MetaDoAviso(feitas=2, meta=4)
    assert aviso.tipo == "tarefa"


def test_rn50_meta_atingida_nao_avisa() -> None:
    assert avisos(tarefas=[meta(4), meta(5)], hoje=date(2026, 10, 29)) == []


# Ordem (RN-51)


def test_rn51_ordenacao() -> None:
    resultado = avisos(
        lembretes=[
            lembrete(date(2026, 10, 14), antecedencia=0, titulo="Lembrete hoje"),
            lembrete(date(2026, 10, 11), titulo="Vencido"),
        ],
        tarefas=[
            tarefa(date(2026, 10, 16), titulo="Tarefa em 2"),
            tarefa(date(2026, 10, 14), titulo="tarefa b hoje"),
            tarefa(date(2026, 10, 14), titulo="Tarefa A hoje"),
        ],
    )

    assert resultado == [
        ("Vencido", -3),
        ("Lembrete hoje", 0),
        ("Tarefa A hoje", 0),
        ("tarefa b hoje", 0),
        ("Tarefa em 2", 2),
    ]


def test_sem_candidatos_sem_avisos() -> None:
    assert calcular_avisos([], [], HOJE, 3) == []
