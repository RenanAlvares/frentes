"""Lixeira: restaurar projeto e tarefa (RN-91, RN-92). Usado pelos Desfazer (1.2 e 1.6)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.conftest import criar_projeto, criar_tarefa


def test_rn92_restaurar_projeto_volta_como_estava(client: TestClient) -> None:
    a = criar_projeto(client, nome="A")
    b = criar_projeto(client, nome="B")
    client.delete(f"/api/projetos/{a['id']}")

    resposta = client.post(f"/api/lixeira/projeto/{a['id']}/restaurar")

    assert resposta.status_code == 204
    assert client.get(f"/api/projetos/{a['id']}").json() == a
    assert [p["id"] for p in client.get("/api/projetos").json()] == [a["id"], b["id"]]


@pytest.mark.parametrize("excluir", [False, True], ids=["nao-excluido", "inexistente"])
def test_restaurar_o_que_nao_esta_na_lixeira_da_404(client: TestClient, excluir: bool) -> None:
    projeto_id = criar_projeto(client)["id"] if not excluir else str(uuid.uuid4())

    resposta = client.post(f"/api/lixeira/projeto/{projeto_id}/restaurar")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["mensagem"] == "Item não encontrado na lixeira."


def test_restaurar_tipo_desconhecido_da_422(client: TestClient) -> None:
    resposta = client.post(f"/api/lixeira/planeta/{uuid.uuid4()}/restaurar")

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["campos"] == {"tipo": "Valor não permitido."}


def test_rn92_restaurar_tarefa_volta_ao_quadro(client: TestClient) -> None:
    projeto_id = criar_projeto(client)["id"]
    tarefa = criar_tarefa(client, projeto_id, titulo="Volta")
    client.delete(f"/api/tarefas/{tarefa['id']}")

    resposta = client.post(f"/api/lixeira/tarefa/{tarefa['id']}/restaurar")

    assert resposta.status_code == 204
    quadro = client.get(f"/api/projetos/{projeto_id}/tarefas").json()
    assert [t["titulo"] for t in quadro["pendente"]] == ["Volta"]


def test_rn91_tarefa_de_projeto_excluido_nao_se_restaura_sozinha(client: TestClient) -> None:
    projeto_id = criar_projeto(client)["id"]
    tarefa = criar_tarefa(client, projeto_id)
    client.delete(f"/api/tarefas/{tarefa['id']}")
    client.delete(f"/api/projetos/{projeto_id}")

    resposta = client.post(f"/api/lixeira/tarefa/{tarefa['id']}/restaurar")

    assert resposta.status_code == 404


def test_restaurar_tarefa_que_nao_esta_na_lixeira_da_404(client: TestClient) -> None:
    tarefa = criar_tarefa(client, criar_projeto(client)["id"])

    resposta = client.post(f"/api/lixeira/tarefa/{tarefa['id']}/restaurar")

    assert resposta.status_code == 404
