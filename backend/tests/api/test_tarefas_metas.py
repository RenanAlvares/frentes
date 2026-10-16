"""Metas mensais: RN-21, RN-24, RN-26 na API. 07 §3.3 (meta); hoje = 2026-10-14."""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.clock import ClockFixo
from tests.conftest import criar_projeto, criar_tarefa


@pytest.fixture
def projeto_id(client: TestClient) -> str:
    return str(criar_projeto(client, nome="Casa", acompanhar_progresso=True)["id"])


def _meta(client: TestClient, projeto_id: str, meta: int = 4, **campos: object) -> dict[str, Any]:
    return criar_tarefa(client, projeto_id, tipo="meta_mensal", meta_mensal=meta, **campos)


def _mais_um(client: TestClient, tarefa: dict[str, Any]) -> dict[str, Any]:
    resposta = client.post(f"/api/tarefas/{tarefa['id']}/concluir")
    assert resposta.status_code == 200, resposta.text
    dados: dict[str, Any] = resposta.json()
    return dados


def _quadro(client: TestClient, projeto_id: str) -> dict[str, Any]:
    quadro: dict[str, Any] = client.get(f"/api/projetos/{projeto_id}/tarefas").json()
    return quadro


def _titulos(quadro: dict[str, Any], coluna: str) -> list[str]:
    return [t["titulo"] for t in quadro[coluna]]


def _campos_invalidos(resposta: Any) -> dict[str, str]:
    assert resposta.status_code == 422, resposta.text
    campos: dict[str, str] = resposta.json()["erro"]["campos"]
    return campos


# RN-21


def test_rn21_criar_meta(client: TestClient, projeto_id: str) -> None:
    meta = _meta(client, projeto_id, titulo="Correr")

    assert meta["tipo"] == "meta_mensal"
    assert meta["meta_mensal"] == 4
    assert meta["progresso_mes"] == 0
    assert meta["status"] == "pendente"
    assert meta["prazo"] is None
    assert meta["recorrencia"] is None
    assert meta["atrasada"] is False


@pytest.mark.parametrize(
    ("campos", "erros"),
    [
        ({}, {"meta_mensal": "Informe quantas vezes por mês."}),
        ({"meta_mensal": 4, "prazo": "2026-10-20"}, {"prazo": "Meta mensal não tem prazo."}),
        (
            {"meta_mensal": 4, "recorrencia": {"frequencia": "diaria"}},
            {"recorrencia": "Meta mensal não tem repetição."},
        ),
        ({"meta_mensal": 0}, {"meta_mensal": "Informe um valor maior ou igual a 1."}),
        ({"meta_mensal": 32}, {"meta_mensal": "Informe um valor menor ou igual a 31."}),
    ],
)
def test_rn21_meta_invalida(
    client: TestClient, projeto_id: str, campos: dict[str, object], erros: dict[str, str]
) -> None:
    resposta = client.post(
        f"/api/projetos/{projeto_id}/tarefas", json={"titulo": "A", "tipo": "meta_mensal", **campos}
    )

    assert _campos_invalidos(resposta) == erros


# RN-24: +1, progresso do mês e coluna derivada


def test_rn24_mais_um_tres_vezes_em_outubro(client: TestClient, projeto_id: str) -> None:
    meta = _meta(client, projeto_id)

    for _ in range(3):
        resposta = _mais_um(client, meta)

    assert resposta["progresso_mes"] == 3
    assert resposta["status"] == "pendente"
    assert resposta["concluida_em"] is None


def test_rn24_atingir_a_meta_leva_para_concluida_e_pode_passar(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    meta = _meta(client, projeto_id, titulo="Correr")
    for dia in (1, 2, 3):
        relogio.definir(date(2026, 10, dia))
        _mais_um(client, meta)
    relogio.definir(date(2026, 10, 9))
    atingiu = _mais_um(client, meta)
    relogio.definir(date(2026, 10, 14))
    passou = _mais_um(client, meta)

    assert atingiu["status"] == "concluida"
    assert atingiu["concluida_em"] == "2026-10-09T15:00:00Z"
    assert passou["progresso_mes"] == 5
    # Passar da meta (5/4) não muda quando ela foi atingida.
    assert passou["concluida_em"] == "2026-10-09T15:00:00Z"
    quadro = _quadro(client, projeto_id)
    assert _titulos(quadro, "pendente") == []
    assert _titulos(quadro, "concluida") == ["Correr"]
    assert quadro["total_concluidas"] == 1


def test_rn24_virada_de_mes_zera_o_progresso(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    meta = _meta(client, projeto_id, meta=2, titulo="Correr")
    _mais_um(client, meta)
    _mais_um(client, meta)
    assert _quadro(client, projeto_id)["concluida"][0]["titulo"] == "Correr"

    relogio.definir(date(2026, 11, 1))

    detalhe = client.get(f"/api/tarefas/{meta['id']}").json()
    assert detalhe["progresso_mes"] == 0
    assert detalhe["status"] == "pendente"
    assert detalhe["execucoes"] == []
    quadro = _quadro(client, projeto_id)
    assert _titulos(quadro, "pendente") == ["Correr"]
    assert quadro["total_concluidas"] == 0


def test_rn24_concluida_ordenada_pela_data_em_que_a_meta_foi_atingida(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    antes = criar_tarefa(client, projeto_id, titulo="Antes")
    depois = criar_tarefa(client, projeto_id, titulo="Depois")
    meta = _meta(client, projeto_id, meta=1, titulo="Meta")
    relogio.definir(date(2026, 10, 10))
    client.post(f"/api/tarefas/{antes['id']}/concluir")
    relogio.definir(date(2026, 10, 11))
    _mais_um(client, meta)
    relogio.definir(date(2026, 10, 12))
    client.post(f"/api/tarefas/{depois['id']}/concluir")

    quadro = _quadro(client, projeto_id)
    todas = client.get(f"/api/projetos/{projeto_id}/tarefas/concluidas").json()

    assert _titulos(quadro, "concluida") == ["Depois", "Meta", "Antes"]
    assert [t["titulo"] for t in todas] == ["Depois", "Meta", "Antes"]
    assert quadro["total_concluidas"] == 3


def test_detalhe_mostra_as_execucoes_do_mes(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    meta = _meta(client, projeto_id)
    relogio.definir(date(2026, 9, 30))
    _mais_um(client, meta)
    for dia in (2, 5):
        relogio.definir(date(2026, 10, dia))
        _mais_um(client, meta)

    detalhe = client.get(f"/api/tarefas/{meta['id']}").json()

    assert [e["data"] for e in detalhe["execucoes"]] == ["2026-10-05", "2026-10-02"]
    assert detalhe["progresso_mes"] == 2


# RN-24 "-1" e RN-26


@pytest.mark.parametrize("rota", ["execucoes/remover-ultima", "desfazer-conclusao"])
def test_rn24_rn26_menos_um_apaga_a_execucao_mais_recente_do_mes(
    client: TestClient, projeto_id: str, rota: str
) -> None:
    meta = _meta(client, projeto_id)
    _mais_um(client, meta)
    _mais_um(client, meta)

    resposta = client.post(f"/api/tarefas/{meta['id']}/{rota}")

    assert resposta.status_code == 200
    assert resposta.json()["progresso_mes"] == 1


@pytest.mark.parametrize("rota", ["execucoes/remover-ultima", "desfazer-conclusao"])
def test_rn24_menos_um_sem_execucoes_no_mes_da_409(
    client: TestClient, projeto_id: str, relogio: ClockFixo, rota: str
) -> None:
    meta = _meta(client, projeto_id)
    _mais_um(client, meta)
    relogio.definir(date(2026, 11, 1))

    resposta = client.post(f"/api/tarefas/{meta['id']}/{rota}")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["mensagem"] == "Não há execuções neste mês."


def test_menos_um_so_para_metas(client: TestClient, projeto_id: str) -> None:
    simples = criar_tarefa(client, projeto_id)

    resposta = client.post(f"/api/tarefas/{simples['id']}/execucoes/remover-ultima")

    assert resposta.status_code == 409


# RN-24: colunas


@pytest.mark.parametrize("status", ["em_andamento", "concluida"])
def test_rn24_mover_meta_para_outra_coluna_da_409(
    client: TestClient, projeto_id: str, status: str
) -> None:
    meta = _meta(client, projeto_id)

    resposta = client.post(f"/api/tarefas/{meta['id']}/mover", json={"status": status, "indice": 0})

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["mensagem"] == "Meta mensal não muda de coluna; use +1 e -1."


def test_rn24_meta_atingida_nao_volta_para_pendente_arrastando(
    client: TestClient, projeto_id: str
) -> None:
    meta = _meta(client, projeto_id, meta=1)
    _mais_um(client, meta)

    para_pendente = client.post(
        f"/api/tarefas/{meta['id']}/mover", json={"status": "pendente", "indice": 0}
    )
    na_concluida = client.post(
        f"/api/tarefas/{meta['id']}/mover", json={"status": "concluida", "indice": 3}
    )

    assert para_pendente.status_code == 409
    assert na_concluida.status_code == 200


def test_rn24_reordenar_meta_dentro_de_pendente_ignora_metas_atingidas(
    client: TestClient, projeto_id: str
) -> None:
    atingida = _meta(client, projeto_id, meta=1, titulo="Atingida")
    _mais_um(client, atingida)
    criar_tarefa(client, projeto_id, titulo="B")
    meta = _meta(client, projeto_id, titulo="Meta")
    criar_tarefa(client, projeto_id, titulo="A")
    assert _titulos(_quadro(client, projeto_id), "pendente") == ["A", "Meta", "B"]

    quadro = client.post(
        f"/api/tarefas/{meta['id']}/mover", json={"status": "pendente", "indice": 2}
    ).json()

    assert _titulos(quadro, "pendente") == ["A", "B", "Meta"]
    assert [t["posicao"] for t in quadro["pendente"]] == [0, 1, 2]
    assert _titulos(quadro, "concluida") == ["Atingida"]


def test_rn24_patch_de_status_em_meta_da_409(client: TestClient, projeto_id: str) -> None:
    meta = _meta(client, projeto_id)

    resposta = client.patch(f"/api/tarefas/{meta['id']}", json={"status": "concluida"})

    assert resposta.status_code == 409


def test_rn21_virar_meta_vai_para_o_topo_de_pendente_e_voltar_mantem_execucoes(
    client: TestClient, projeto_id: str
) -> None:
    outra = criar_tarefa(client, projeto_id, titulo="Outra")
    tarefa = criar_tarefa(client, projeto_id, titulo="Virou meta")
    client.post(f"/api/tarefas/{tarefa['id']}/mover", json={"status": "em_andamento", "indice": 0})
    url = f"/api/tarefas/{tarefa['id']}"

    virou = client.patch(url, json={"tipo": "meta_mensal", "meta_mensal": 3})
    assert virou.json()["status"] == "pendente"
    assert _titulos(_quadro(client, projeto_id), "pendente") == ["Virou meta", outra["titulo"]]
    _mais_um(client, virou.json())

    voltou = client.patch(url, json={"tipo": "simples", "meta_mensal": None})
    assert voltou.json()["tipo"] == "simples"
    assert voltou.json()["progresso_mes"] is None

    de_novo = client.patch(url, json={"tipo": "meta_mensal", "meta_mensal": 3})
    assert de_novo.json()["progresso_mes"] == 1


# RN-27 e RN-13


def test_meta_nunca_e_atrasada_nem_conta_no_progresso_do_projeto(
    client: TestClient, projeto_id: str
) -> None:
    meta = _meta(client, projeto_id, meta=1)
    _mais_um(client, meta)
    criar_tarefa(client, projeto_id)

    assert client.get(f"/api/tarefas/{meta['id']}").json()["atrasada"] is False
    progresso = client.get(f"/api/projetos/{projeto_id}").json()["progresso"]
    assert progresso == {"concluidas": 0, "total": 1}
