"""Tarefas de hoje: RN-60..62 na API (e RN-12). 07 §3.5; hoje = 2026-10-14 (quarta)."""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.clock import ClockFixo
from tests.conftest import criar_projeto, criar_tarefa

QUARTA = {"frequencia": "semanal", "dias_semana": [2]}


@pytest.fixture
def projeto(client: TestClient) -> dict[str, Any]:
    return criar_projeto(client, nome="Casa", cor="verde")


def _hoje(client: TestClient) -> dict[str, Any]:
    resposta = client.get("/api/tarefas/hoje")
    assert resposta.status_code == 200, resposta.text
    listas: dict[str, Any] = resposta.json()
    return listas


def _titulos(client: TestClient) -> dict[str, list[str]]:
    listas = _hoje(client)
    return {nome: [t["titulo"] for t in listas[nome]] for nome in ("atrasadas", "hoje")}


def test_rn60_rn61_hoje_atrasadas_e_futuras(client: TestClient, projeto: dict[str, Any]) -> None:
    pid = projeto["id"]
    criar_tarefa(client, pid, titulo="Hoje", prazo="2026-10-14")
    criar_tarefa(
        client, pid, titulo="Repete hoje", tipo="repetida", prazo="2026-10-14", recorrencia=QUARTA
    )
    andamento = criar_tarefa(client, pid, titulo="Em andamento", prazo="2026-10-14")
    client.patch(f"/api/tarefas/{andamento['id']}", json={"status": "em_andamento"})
    criar_tarefa(client, pid, titulo="Atrasada", prazo="2026-10-10")
    criar_tarefa(client, pid, titulo="Amanhã", prazo="2026-10-15")
    criar_tarefa(client, pid, titulo="Sem prazo")
    concluida = criar_tarefa(client, pid, titulo="Concluída", prazo="2026-10-14")
    client.post(f"/api/tarefas/{concluida['id']}/concluir")
    excluida = criar_tarefa(client, pid, titulo="Excluída", prazo="2026-10-10")
    client.delete(f"/api/tarefas/{excluida['id']}")

    assert _titulos(client) == {
        "atrasadas": ["Atrasada"],
        "hoje": ["Em andamento", "Hoje", "Repete hoje"],
    }


def test_tarefa_hoje_traz_o_projeto(client: TestClient, projeto: dict[str, Any]) -> None:
    tarefa = criar_tarefa(client, projeto["id"], titulo="Atrasada", prazo="2026-10-10")

    (item,) = _hoje(client)["atrasadas"]
    assert item == {
        **tarefa,
        "atrasada": True,
        "projeto": {"id": projeto["id"], "nome": "Casa", "cor": "verde"},
    }


def test_rn60_meta_incompleta_no_ultimo_dia_do_mes(
    client: TestClient, relogio: ClockFixo, projeto: dict[str, Any]
) -> None:
    pid = projeto["id"]
    incompleta = criar_tarefa(client, pid, titulo="Correr", tipo="meta_mensal", meta_mensal=4)
    completa = criar_tarefa(client, pid, titulo="Ler", tipo="meta_mensal", meta_mensal=1)
    client.post(f"/api/tarefas/{incompleta['id']}/concluir")
    client.post(f"/api/tarefas/{completa['id']}/concluir")
    assert _titulos(client) == {"atrasadas": [], "hoje": []}

    relogio.definir(date(2026, 10, 31))
    (item,) = _hoje(client)["hoje"]
    assert item["titulo"] == "Correr"
    assert item["progresso_mes"] == 1
    assert item["meta_mensal"] == 4

    # Virada de mês: o progresso zera, mas 01/11 não é o último dia.
    relogio.definir(date(2026, 11, 1))
    assert _titulos(client) == {"atrasadas": [], "hoje": []}


def test_rn12_projeto_concluido_ou_excluido_sai_da_lista(client: TestClient) -> None:
    ativo = criar_projeto(client, nome="Ativo")["id"]
    criar_tarefa(client, ativo, titulo="Fica", prazo="2026-10-14")
    arquivado = criar_projeto(client, nome="Arquivado")["id"]
    criar_tarefa(client, arquivado, titulo="Do concluído", prazo="2026-10-14")
    criar_tarefa(client, arquivado, titulo="Atrasada do concluído", prazo="2026-10-01")
    client.patch(f"/api/projetos/{arquivado}", json={"status": "concluido"})
    lixo = criar_projeto(client, nome="Lixo")["id"]
    criar_tarefa(client, lixo, titulo="Do excluído", prazo="2026-10-14")
    client.delete(f"/api/projetos/{lixo}")

    assert _titulos(client) == {"atrasadas": [], "hoje": ["Fica"]}


def test_rn62_ordenacao(client: TestClient) -> None:
    beta = criar_projeto(client, nome="beta")["id"]
    alfa = criar_projeto(client, nome="Alfa")["id"]
    criar_tarefa(client, beta, titulo="baixa", prioridade="baixa", prazo="2026-10-14")
    criar_tarefa(client, beta, titulo="alta beta", prioridade="alta", prazo="2026-10-14")
    criar_tarefa(client, alfa, titulo="b alta alfa", prioridade="alta", prazo="2026-10-14")
    criar_tarefa(client, alfa, titulo="A alta alfa", prioridade="alta", prazo="2026-10-14")
    criar_tarefa(client, alfa, titulo="média", prazo="2026-10-14")

    criar_tarefa(client, beta, titulo="Dia 12 alta", prioridade="alta", prazo="2026-10-12")
    criar_tarefa(client, alfa, titulo="Dia 12 baixa", prioridade="baixa", prazo="2026-10-12")
    criar_tarefa(client, beta, titulo="Dia 5 baixa", prioridade="baixa", prazo="2026-10-05")

    assert _titulos(client) == {
        "atrasadas": ["Dia 5 baixa", "Dia 12 alta", "Dia 12 baixa"],
        "hoje": ["A alta alfa", "b alta alfa", "alta beta", "média", "baixa"],
    }


def test_sem_tarefas(client: TestClient) -> None:
    assert _hoje(client) == {"atrasadas": [], "hoje": []}
