"""Lixeira: restaurar projeto (RN-92). Usado pelo Desfazer da home (1.2)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.conftest import criar_projeto


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
