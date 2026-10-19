"""Avisos: RN-50..58 na API. 07 §3.2; hoje = 2026-10-14 (quarta)."""

from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from app.clock import ClockFixo
from app.models import Configuracao
from tests.conftest import criar_lembrete, criar_projeto, criar_tarefa


@pytest.fixture
def projeto(client: TestClient) -> dict[str, Any]:
    return criar_projeto(client, nome="Casa", cor="verde")


def _avisos(client: TestClient) -> dict[str, Any]:
    resposta = client.get("/api/avisos")
    assert resposta.status_code == 200, resposta.text
    avisos: dict[str, Any] = resposta.json()
    assert avisos["total"] == len(avisos["itens"])
    return avisos


def _titulos(client: TestClient) -> list[str]:
    return [item["titulo"] for item in _avisos(client)["itens"]]


def _restantes(client: TestClient) -> dict[str, int]:
    return {item["titulo"]: item["dias_restantes"] for item in _avisos(client)["itens"]}


def test_rn56_formato_do_aviso_de_lembrete(client: TestClient, projeto: dict[str, Any]) -> None:
    lembrete = criar_lembrete(
        client, projeto["id"], titulo="IPTU", vencimento="2026-10-17", antecedencia_dias=3
    )

    assert _avisos(client) == {
        "total": 1,
        "itens": [
            {
                "tipo": "lembrete",
                "id": lembrete["id"],
                "titulo": "IPTU",
                "projeto": {"id": projeto["id"], "nome": "Casa", "cor": "verde"},
                "vencimento": "2026-10-17",
                "dias_restantes": 3,
                "ocorrencias_atrasadas": 0,
                "meta": None,
            }
        ],
    }


def test_rn42_janela_do_lembrete(client: TestClient, projeto: dict[str, Any]) -> None:
    pid = projeto["id"]
    criar_lembrete(client, pid, titulo="Dia 17", vencimento="2026-10-17", antecedencia_dias=3)
    criar_lembrete(client, pid, titulo="Dia 18", vencimento="2026-10-18", antecedencia_dias=3)
    criar_lembrete(client, pid, titulo="Hoje", vencimento="2026-10-14", antecedencia_dias=0)
    criar_lembrete(client, pid, titulo="Vencido", vencimento="2026-10-11")

    assert _restantes(client) == {"Vencido": -3, "Hoje": 0, "Dia 17": 3}


def test_rn34_ocorrencias_atrasadas_do_lembrete_recorrente(
    client: TestClient, projeto: dict[str, Any]
) -> None:
    mensal = {"frequencia": "mensal", "dia_mes": 5}
    criar_lembrete(client, projeto["id"], vencimento="2026-08-05", recorrencia=mensal)

    (item,) = _avisos(client)["itens"]
    assert item["ocorrencias_atrasadas"] == 3
    assert item["dias_restantes"] == -70


def test_rn41_rn50_lembretes_que_nao_avisam(client: TestClient) -> None:
    casa = criar_projeto(client, nome="Casa")["id"]
    concluido = criar_lembrete(client, casa, titulo="Concluído", vencimento="2026-10-11")
    client.post(f"/api/lembretes/{concluido['id']}/baixa")
    excluido = criar_lembrete(client, casa, titulo="Excluído", vencimento="2026-10-11")
    client.delete(f"/api/lembretes/{excluido['id']}")
    criar_lembrete(client, casa, titulo="Fica", vencimento="2026-10-11")

    arquivado = criar_projeto(client, nome="Arquivado")["id"]
    criar_lembrete(client, arquivado, titulo="Do concluído", vencimento="2026-10-11")
    client.patch(f"/api/projetos/{arquivado}", json={"status": "concluido"})
    lixo = criar_projeto(client, nome="Lixo")["id"]
    criar_lembrete(client, lixo, titulo="Do excluído", vencimento="2026-10-11")
    client.delete(f"/api/projetos/{lixo}")

    assert _titulos(client) == ["Fica"]


def test_rn50_tarefas_com_prazo_na_janela(client: TestClient, projeto: dict[str, Any]) -> None:
    pid = projeto["id"]
    tarefa = criar_tarefa(client, pid, titulo="Dia 17", prazo="2026-10-17")
    criar_tarefa(client, pid, titulo="Dia 18", prazo="2026-10-18")
    criar_tarefa(client, pid, titulo="Sem prazo")
    concluida = criar_tarefa(client, pid, titulo="Concluída", prazo="2026-10-10")
    client.post(f"/api/tarefas/{concluida['id']}/concluir")
    excluida = criar_tarefa(client, pid, titulo="Excluída", prazo="2026-10-10")
    client.delete(f"/api/tarefas/{excluida['id']}")

    (item,) = _avisos(client)["itens"]
    assert item == {
        "tipo": "tarefa",
        "id": tarefa["id"],
        "titulo": "Dia 17",
        "projeto": {"id": pid, "nome": "Casa", "cor": "verde"},
        "vencimento": "2026-10-17",
        "dias_restantes": 3,
        "ocorrencias_atrasadas": 0,
        "meta": None,
    }


def test_rn50_aviso_tarefas_dias_vem_da_configuracao(
    client: TestClient, app: FastAPI, projeto: dict[str, Any]
) -> None:
    criar_tarefa(client, projeto["id"], titulo="Dia 17", prazo="2026-10-17")
    criar_tarefa(client, projeto["id"], titulo="Hoje", prazo="2026-10-14")
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        sessao.execute(
            update(Configuracao).where(Configuracao.chave == "aviso_tarefas_dias").values(valor=0)
        )
        sessao.commit()

    assert _titulos(client) == ["Hoje"]


def test_rn50_meta_mensal_avisa_perto_do_fim_do_mes(
    client: TestClient, relogio: ClockFixo, projeto: dict[str, Any]
) -> None:
    meta = criar_tarefa(client, projeto["id"], titulo="Correr", tipo="meta_mensal", meta_mensal=4)
    for _ in range(2):
        client.post(f"/api/tarefas/{meta['id']}/concluir")
    assert _titulos(client) == []

    relogio.definir(date(2026, 10, 29))
    (item,) = _avisos(client)["itens"]
    assert item["vencimento"] == "2026-10-31"
    assert item["dias_restantes"] == 2
    assert item["meta"] == {"feitas": 2, "meta": 4}

    for _ in range(2):
        client.post(f"/api/tarefas/{meta['id']}/concluir")
    assert _titulos(client) == []


def test_rn51_ordenacao(client: TestClient, projeto: dict[str, Any]) -> None:
    pid = projeto["id"]
    criar_tarefa(client, pid, titulo="Tarefa 2", prazo="2026-10-16")
    criar_tarefa(client, pid, titulo="b tarefa 0", prazo="2026-10-14")
    criar_tarefa(client, pid, titulo="A tarefa 0", prazo="2026-10-14")
    criar_lembrete(client, pid, titulo="Lembrete 0", vencimento="2026-10-14")
    criar_lembrete(client, pid, titulo="Vencido", vencimento="2026-10-11")

    assert _titulos(client) == ["Vencido", "Lembrete 0", "A tarefa 0", "b tarefa 0", "Tarefa 2"]


def test_sem_avisos(client: TestClient) -> None:
    assert _avisos(client) == {"total": 0, "itens": []}


def test_rn57_contador_de_avisos_do_projeto(client: TestClient) -> None:
    casa = criar_projeto(client, nome="Casa")["id"]
    criar_lembrete(client, casa, vencimento="2026-10-11")
    criar_tarefa(client, casa, prazo="2026-10-15")
    criar_tarefa(client, casa, prazo="2026-10-30")
    trabalho = criar_projeto(client, nome="Trabalho")["id"]
    criar_lembrete(client, trabalho, vencimento="2026-12-01")
    arquivado = criar_projeto(client, nome="Arquivado")["id"]
    criar_lembrete(client, arquivado, vencimento="2026-10-11")
    client.patch(f"/api/projetos/{arquivado}", json={"status": "concluido"})

    ativos = client.get("/api/projetos").json()
    assert {p["nome"]: p["avisos"] for p in ativos} == {"Casa": 2, "Trabalho": 0}
    assert client.get(f"/api/projetos/{casa}").json()["avisos"] == 2
    (concluido,) = client.get("/api/projetos", params={"arquivados": True}).json()
    assert concluido["avisos"] == 0
