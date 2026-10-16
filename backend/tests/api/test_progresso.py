"""RN-13: progresso do projeto conta só tarefas simples não excluídas. 07 §3.3."""

import uuid
from datetime import UTC, date, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models import Tarefa
from tests.conftest import criar_projeto, criar_tarefa


def _progresso(client: TestClient, projeto_id: str) -> Any:
    detalhe = client.get(f"/api/projetos/{projeto_id}").json()["progresso"]
    (resumo,) = [p for p in client.get("/api/projetos").json() if p["id"] == projeto_id]
    assert resumo["progresso"] == detalhe, "lista e detalhe devem concordar"
    return detalhe


def _inserir(app: FastAPI, projeto_id: str, **campos: object) -> None:
    """Repetidas e metas ainda não são criadas pela API (fase 2); entram direto no banco."""
    agora = datetime(2026, 10, 14, 15, tzinfo=UTC)
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        sessao.add(
            Tarefa(
                projeto_id=uuid.UUID(projeto_id),
                titulo="X",
                descricao="",
                status="pendente",
                prioridade="media",
                posicao=0,
                busca="x",
                criado_em=agora,
                atualizado_em=agora,
                **campos,
            )
        )
        sessao.commit()


def test_rn13_conta_concluidas_sobre_o_total_de_simples(client: TestClient) -> None:
    projeto_id = criar_projeto(client, acompanhar_progresso=True)["id"]
    tarefas = [criar_tarefa(client, projeto_id, titulo=f"T{i}") for i in range(4)]
    for tarefa in tarefas[:3]:
        client.post(f"/api/tarefas/{tarefa['id']}/concluir")
    client.post(f"/api/tarefas/{tarefas[1]['id']}/desfazer-conclusao")

    assert _progresso(client, projeto_id) == {"concluidas": 2, "total": 4}


def test_rn13_em_andamento_conta_no_total_mas_nao_como_concluida(client: TestClient) -> None:
    projeto_id = criar_projeto(client, acompanhar_progresso=True)["id"]
    tarefa = criar_tarefa(client, projeto_id)
    client.post(f"/api/tarefas/{tarefa['id']}/mover", json={"status": "em_andamento", "indice": 0})

    assert _progresso(client, projeto_id) == {"concluidas": 0, "total": 1}


def test_rn13_tarefa_excluida_nao_conta(client: TestClient) -> None:
    projeto_id = criar_projeto(client, acompanhar_progresso=True)["id"]
    feita = criar_tarefa(client, projeto_id)
    criar_tarefa(client, projeto_id)
    client.post(f"/api/tarefas/{feita['id']}/concluir")

    client.delete(f"/api/tarefas/{feita['id']}")

    assert _progresso(client, projeto_id) == {"concluidas": 0, "total": 1}


def test_rn13_repetidas_e_metas_nao_entram(client: TestClient, app: FastAPI) -> None:
    projeto_id = criar_projeto(client, acompanhar_progresso=True)["id"]
    criar_tarefa(client, projeto_id)
    _inserir(
        app,
        projeto_id,
        tipo="repetida",
        prazo=date(2026, 10, 20),
        recorrencia={"frequencia": "diaria", "intervalo": 1},
    )
    _inserir(app, projeto_id, tipo="meta_mensal", meta_mensal=4)

    assert _progresso(client, projeto_id) == {"concluidas": 0, "total": 1}


def test_rn13_sem_tarefas_e_zero_de_zero(client: TestClient) -> None:
    projeto_id = criar_projeto(client, acompanhar_progresso=True)["id"]

    assert _progresso(client, projeto_id) == {"concluidas": 0, "total": 0}


def test_rn13_sem_acompanhamento_o_progresso_e_nulo(client: TestClient) -> None:
    projeto_id = criar_projeto(client)["id"]
    criar_tarefa(client, projeto_id)

    assert _progresso(client, projeto_id) is None

    resposta = client.patch(f"/api/projetos/{projeto_id}", json={"acompanhar_progresso": True})

    assert resposta.json()["progresso"] == {"concluidas": 0, "total": 1}


def test_rn13_cada_projeto_com_sua_contagem(client: TestClient) -> None:
    a = criar_projeto(client, nome="A", acompanhar_progresso=True)["id"]
    b = criar_projeto(client, nome="B", acompanhar_progresso=True)["id"]
    for _ in range(3):
        criar_tarefa(client, a)
    client.post(f"/api/tarefas/{criar_tarefa(client, b)['id']}/concluir")

    progressos = {p["nome"]: p["progresso"] for p in client.get("/api/projetos").json()}

    assert progressos == {"A": {"concluidas": 0, "total": 3}, "B": {"concluidas": 1, "total": 1}}
