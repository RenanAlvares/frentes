"""Configurações: RN-100 na API. Hoje = 2026-10-14."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from app.models import Configuracao
from tests.conftest import criar_lembrete, criar_projeto, criar_tarefa

PADROES = {"aviso_tarefas_dias": 3, "antecedencia_padrao_lembretes": 3}


def test_rn100_padroes(client: TestClient) -> None:
    resposta = client.get("/api/configuracoes")

    assert resposta.status_code == 200
    assert resposta.json() == PADROES


def test_rn100_patch_muda_so_o_que_foi_enviado(client: TestClient) -> None:
    resposta = client.patch("/api/configuracoes", json={"antecedencia_padrao_lembretes": 7})

    assert resposta.status_code == 200, resposta.text
    esperado = {**PADROES, "antecedencia_padrao_lembretes": 7}
    assert resposta.json() == esperado
    assert client.get("/api/configuracoes").json() == esperado


def test_rn100_limites_0_e_60_sao_aceitos(client: TestClient) -> None:
    resposta = client.patch(
        "/api/configuracoes", json={"aviso_tarefas_dias": 0, "antecedencia_padrao_lembretes": 60}
    )

    assert resposta.json() == {"aviso_tarefas_dias": 0, "antecedencia_padrao_lembretes": 60}


def test_rn100_valores_invalidos_dao_422(client: TestClient) -> None:
    for corpo in (
        {"aviso_tarefas_dias": -1},
        {"aviso_tarefas_dias": 61},
        {"antecedencia_padrao_lembretes": None},
        {"antecedencia_padrao_lembretes": "dez"},
    ):
        resposta = client.patch("/api/configuracoes", json=corpo)
        assert resposta.status_code == 422, corpo
        assert set(resposta.json()["erro"]["campos"]) == set(corpo)

    assert client.get("/api/configuracoes").json() == PADROES


def test_rn100_valor_fora_do_formato_no_banco_vale_o_padrao(
    client: TestClient, app: FastAPI
) -> None:
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        sessao.execute(
            update(Configuracao)
            .where(Configuracao.chave == "aviso_tarefas_dias")
            .values(valor="três")
        )
        sessao.commit()

    assert client.get("/api/configuracoes").json() == PADROES


def test_rn100_aviso_tarefas_dias_muda_os_avisos(client: TestClient) -> None:
    projeto_id = criar_projeto(client, nome="Casa")["id"]
    criar_tarefa(client, projeto_id, titulo="Dia 17", prazo="2026-10-17")
    criar_tarefa(client, projeto_id, titulo="Dia 20", prazo="2026-10-20")

    def titulos() -> list[str]:
        return [a["titulo"] for a in client.get("/api/avisos").json()["itens"]]

    assert titulos() == ["Dia 17"]
    client.patch("/api/configuracoes", json={"aviso_tarefas_dias": 6})
    assert titulos() == ["Dia 17", "Dia 20"]
    assert client.get(f"/api/projetos/{projeto_id}").json()["avisos"] == 2
    client.patch("/api/configuracoes", json={"aviso_tarefas_dias": 0})
    assert titulos() == []


def test_rn40_antecedencia_padrao_vale_para_novos_lembretes(client: TestClient) -> None:
    projeto_id = criar_projeto(client)["id"]
    antes = criar_lembrete(client, projeto_id)

    client.patch("/api/configuracoes", json={"antecedencia_padrao_lembretes": 10})

    assert criar_lembrete(client, projeto_id)["antecedencia_dias"] == 10
    # Os que já existiam não mudam.
    lembretes = client.get(f"/api/projetos/{projeto_id}/lembretes").json()["ativos"]
    assert {lb["id"]: lb["antecedencia_dias"] for lb in lembretes}[antes["id"]] == 3
