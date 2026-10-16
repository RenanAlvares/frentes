"""Tarefas repetidas: RN-21, RN-23, RN-26, RN-35 na API. 07 §3.3 (repetida); hoje = 2026-10-14."""

import uuid
from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.clock import ClockFixo
from app.models import TarefaExecucao
from tests.conftest import criar_projeto, criar_tarefa

SEGUNDA = {"frequencia": "semanal", "intervalo": 1, "dias_semana": [0]}
DIA_5 = {"frequencia": "mensal", "dia_mes": 5}


@pytest.fixture
def projeto_id(client: TestClient) -> str:
    return str(criar_projeto(client, nome="Casa")["id"])


def _repetida(client: TestClient, projeto_id: str, **campos: object) -> dict[str, Any]:
    dados: dict[str, object] = {"tipo": "repetida", "prazo": "2026-10-19", "recorrencia": SEGUNDA}
    return criar_tarefa(client, projeto_id, **{**dados, **campos})


def _tarefa(client: TestClient, tarefa: dict[str, Any]) -> dict[str, Any]:
    detalhe: dict[str, Any] = client.get(f"/api/tarefas/{tarefa['id']}").json()
    return detalhe


def _campos_invalidos(resposta: Any) -> dict[str, str]:
    assert resposta.status_code == 422, resposta.text
    campos: dict[str, str] = resposta.json()["erro"]["campos"]
    return campos


def _quantas_execucoes(app: FastAPI, tarefa_id: str) -> int:
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        consulta = select(func.count()).where(TarefaExecucao.tarefa_id == uuid.UUID(tarefa_id))
        return sessao.scalar(consulta) or 0


# Criar e RN-21


def test_rn21_criar_repetida_com_descricao_da_regra(client: TestClient, projeto_id: str) -> None:
    tarefa = _repetida(
        client, projeto_id, recorrencia={"frequencia": "semanal", "dias_semana": [2, 0]}
    )

    assert tarefa["tipo"] == "repetida"
    assert tarefa["prazo"] == "2026-10-19"
    assert tarefa["recorrencia"] == {
        "frequencia": "semanal",
        "intervalo": 1,
        "dias_semana": [0, 2],
        "dia_mes": None,
        "mes": None,
    }
    assert tarefa["recorrencia_descricao"] == "toda semana: segunda e quarta"
    assert tarefa["status"] == "pendente"


@pytest.mark.parametrize(
    ("campos", "erros"),
    [
        (
            {"tipo": "repetida"},
            {"prazo": "Informe a primeira data.", "recorrencia": "Informe a repetição."},
        ),
        ({"tipo": "repetida", "recorrencia": SEGUNDA}, {"prazo": "Informe a primeira data."}),
        ({"tipo": "repetida", "prazo": "2026-10-19"}, {"recorrencia": "Informe a repetição."}),
        (
            {"tipo": "repetida", "prazo": "2026-10-19", "recorrencia": SEGUNDA, "meta_mensal": 3},
            {"meta_mensal": "Tarefa repetida não tem meta mensal."},
        ),
        (
            {"tipo": "repetida", "prazo": "2026-10-19", "recorrencia": {"frequencia": "semanal"}},
            {"recorrencia.dias_semana": "Escolha pelo menos um dia da semana."},
        ),
        (
            {"tipo": "simples", "recorrencia": SEGUNDA},
            {"recorrencia": "Tarefa simples não tem repetição."},
        ),
    ],
)
def test_rn21_rn30_criar_invalido(
    client: TestClient, projeto_id: str, campos: dict[str, object], erros: dict[str, str]
) -> None:
    resposta = client.post(f"/api/projetos/{projeto_id}/tarefas", json={"titulo": "A", **campos})

    assert _campos_invalidos(resposta) == erros


def test_rn21_trocar_tipo_valida_o_novo_tipo_e_mantem_execucoes(
    client: TestClient, app: FastAPI, projeto_id: str
) -> None:
    simples = criar_tarefa(client, projeto_id, prazo="2026-10-19")
    url = f"/api/tarefas/{simples['id']}"

    sem_regra = client.patch(url, json={"tipo": "repetida"})
    assert _campos_invalidos(sem_regra) == {"recorrencia": "Informe a repetição."}

    virou_repetida = client.patch(url, json={"tipo": "repetida", "recorrencia": SEGUNDA})
    assert virou_repetida.json()["recorrencia_descricao"] == "toda segunda"
    client.post(f"{url}/concluir")
    assert _quantas_execucoes(app, simples["id"]) == 1

    com_regra = client.patch(url, json={"tipo": "simples"})
    assert _campos_invalidos(com_regra) == {"recorrencia": "Tarefa simples não tem repetição."}

    voltou = client.patch(url, json={"tipo": "simples", "recorrencia": None})
    assert voltou.json()["tipo"] == "simples"
    assert voltou.json()["recorrencia_descricao"] is None
    assert _quantas_execucoes(app, simples["id"]) == 1


def test_simples_concluida_que_vira_repetida_volta_para_pendente(
    client: TestClient, projeto_id: str
) -> None:
    outra = criar_tarefa(client, projeto_id, titulo="Outra")
    simples = criar_tarefa(client, projeto_id, titulo="Virou", prazo="2026-10-19")
    client.post(f"/api/tarefas/{simples['id']}/concluir")

    resposta = client.patch(
        f"/api/tarefas/{simples['id']}", json={"tipo": "repetida", "recorrencia": SEGUNDA}
    )

    assert resposta.json()["status"] == "pendente"
    assert resposta.json()["concluida_em"] is None
    quadro = client.get(f"/api/projetos/{projeto_id}/tarefas").json()
    assert [t["titulo"] for t in quadro["pendente"]] == ["Virou", outra["titulo"]]
    assert quadro["total_concluidas"] == 0


# RN-23: concluir


@pytest.mark.parametrize("pelo", ["concluir", "patch", "mover"])
def test_rn23_concluir_registra_execucao_avanca_e_fica_pendente(
    client: TestClient, projeto_id: str, pelo: str
) -> None:
    tarefa = _repetida(client, projeto_id, prazo="2026-10-12")
    url = f"/api/tarefas/{tarefa['id']}"

    if pelo == "concluir":
        resposta = client.post(f"{url}/concluir")
    elif pelo == "patch":
        resposta = client.patch(url, json={"status": "concluida"})
    else:
        resposta = client.post(f"{url}/mover", json={"status": "concluida", "indice": 0})
    assert resposta.status_code == 200, resposta.text

    detalhe = _tarefa(client, tarefa)
    assert detalhe["status"] == "pendente"
    assert detalhe["concluida_em"] is None
    # Atrasada desde 12/10 (segunda); hoje 14/10 → a próxima segunda futura.
    assert detalhe["prazo"] == "2026-10-19"
    assert detalhe["execucoes"] == [{"data": "2026-10-14", "criado_em": "2026-10-14T15:00:00Z"}]
    quadro = client.get(f"/api/projetos/{projeto_id}/tarefas").json()
    assert [t["id"] for t in quadro["pendente"]] == [tarefa["id"]]
    assert quadro["concluida"] == []
    assert quadro["total_concluidas"] == 0


def test_rn23_pula_as_ocorrencias_perdidas(client: TestClient, projeto_id: str) -> None:
    tarefa = _repetida(client, projeto_id, prazo="2026-08-05", recorrencia=DIA_5)
    assert tarefa["atrasada"] is True

    concluida = client.post(f"/api/tarefas/{tarefa['id']}/concluir").json()

    assert concluida["prazo"] == "2026-11-05"
    assert concluida["atrasada"] is False


def test_rn23_vinda_de_em_andamento_entra_no_topo_de_pendente(
    client: TestClient, projeto_id: str
) -> None:
    repetida = _repetida(client, projeto_id, titulo="Repetida")
    criar_tarefa(client, projeto_id, titulo="Simples")
    client.post(
        f"/api/tarefas/{repetida['id']}/mover", json={"status": "em_andamento", "indice": 0}
    )

    client.post(f"/api/tarefas/{repetida['id']}/concluir")

    quadro = client.get(f"/api/projetos/{projeto_id}/tarefas").json()
    assert [t["titulo"] for t in quadro["pendente"]] == ["Repetida", "Simples"]
    assert [t["posicao"] for t in quadro["pendente"]] == [0, 1]
    assert quadro["em_andamento"] == []


def test_rn23_ja_pendente_fica_na_mesma_posicao(client: TestClient, projeto_id: str) -> None:
    repetida = _repetida(client, projeto_id, titulo="Repetida")
    criar_tarefa(client, projeto_id, titulo="Simples")

    client.post(f"/api/tarefas/{repetida['id']}/concluir")

    quadro = client.get(f"/api/projetos/{projeto_id}/tarefas").json()
    assert [t["titulo"] for t in quadro["pendente"]] == ["Simples", "Repetida"]


def test_historico_mostra_as_5_execucoes_mais_recentes(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    tarefa = _repetida(client, projeto_id, prazo="2026-10-01", recorrencia={"frequencia": "diaria"})
    for dia in range(1, 8):
        relogio.definir(date(2026, 10, dia))
        client.post(f"/api/tarefas/{tarefa['id']}/concluir")

    execucoes = _tarefa(client, tarefa)["execucoes"]

    assert [e["data"] for e in execucoes] == [f"2026-10-0{dia}" for dia in range(7, 2, -1)]


# RN-26: desfazer


def test_rn26_desfazer_apaga_a_ultima_execucao_e_restaura_o_prazo(
    client: TestClient, app: FastAPI, projeto_id: str, relogio: ClockFixo
) -> None:
    tarefa = _repetida(client, projeto_id, prazo="2026-10-12")
    url = f"/api/tarefas/{tarefa['id']}"
    client.post(f"{url}/concluir")  # 12/10 → 19/10
    relogio.definir(date(2026, 10, 19))
    client.post(f"{url}/concluir")  # 19/10 → 26/10

    primeira = client.post(f"{url}/desfazer-conclusao")
    assert primeira.status_code == 200
    assert primeira.json()["prazo"] == "2026-10-19"
    assert _quantas_execucoes(app, tarefa["id"]) == 1

    segunda = client.post(f"{url}/desfazer-conclusao")
    assert segunda.json()["prazo"] == "2026-10-12"
    assert _quantas_execucoes(app, tarefa["id"]) == 0


def test_rn26_desfazer_repetida_sem_historico_da_409(client: TestClient, projeto_id: str) -> None:
    tarefa = _repetida(client, projeto_id)

    resposta = client.post(f"/api/tarefas/{tarefa['id']}/desfazer-conclusao")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["mensagem"] == "Não há conclusão para desfazer."


# RN-27 e RN-35


def test_rn27_repetida_atrasada(client: TestClient, projeto_id: str) -> None:
    assert _repetida(client, projeto_id, prazo="2026-10-13")["atrasada"] is True
    assert _repetida(client, projeto_id, prazo="2026-10-14")["atrasada"] is False


def test_rn35_descricao_acompanha_a_edicao_da_regra(client: TestClient, projeto_id: str) -> None:
    tarefa = _repetida(client, projeto_id)

    resposta = client.patch(
        f"/api/tarefas/{tarefa['id']}",
        json={"recorrencia": {"frequencia": "mensal", "intervalo": 3, "dia_mes": 10}},
    )

    assert resposta.json()["recorrencia_descricao"] == "a cada 3 meses, no dia 10"
    assert _tarefa(client, tarefa)["recorrencia"]["dia_mes"] == 10


def test_editar_repetida_em_andamento_nao_muda_de_coluna(
    client: TestClient, projeto_id: str
) -> None:
    tarefa = _repetida(client, projeto_id)
    url = f"/api/tarefas/{tarefa['id']}"
    client.post(f"{url}/mover", json={"status": "em_andamento", "indice": 0})

    resposta = client.patch(url, json={"titulo": "Outro título"})

    assert resposta.json()["status"] == "em_andamento"
