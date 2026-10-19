"""Anotações: RN-80..81 na API (e RN-90/91). Hoje = 2026-10-14."""

import uuid
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.clock import ClockFixo
from tests.conftest import criar_projeto


@pytest.fixture
def projeto_id(client: TestClient) -> str:
    return str(criar_projeto(client, nome="Casa")["id"])


def _criar(client: TestClient, projeto_id: str, **campos: object) -> dict[str, Any]:
    resposta = client.post(
        f"/api/projetos/{projeto_id}/anotacoes", json={"texto": "Texto", **campos}
    )
    assert resposta.status_code == 201, resposta.text
    anotacao: dict[str, Any] = resposta.json()
    return anotacao


def _lista(client: TestClient, projeto_id: str) -> list[Any]:
    resposta = client.get(f"/api/projetos/{projeto_id}/anotacoes")
    assert resposta.status_code == 200, resposta.text
    lista: list[Any] = resposta.json()
    return lista


def _campos_invalidos(resposta: Any) -> dict[str, str]:
    assert resposta.status_code == 422, resposta.text
    campos: dict[str, str] = resposta.json()["erro"]["campos"]
    return campos


# RN-80


def test_rn80_criar_com_padroes(client: TestClient, projeto_id: str) -> None:
    anotacao = _criar(client, projeto_id, texto="  Medidas da sala: 4 x 5 m  ")

    assert anotacao == {
        "id": anotacao["id"],
        "projeto_id": projeto_id,
        "titulo": "",
        "texto": "Medidas da sala: 4 x 5 m",
        "cor": "amarelo",
        "fixada": False,
        "criado_em": "2026-10-14T15:00:00Z",
        "atualizado_em": "2026-10-14T15:00:00Z",
    }
    assert _lista(client, projeto_id) == [anotacao]


def test_rn80_criar_com_todos_os_campos(client: TestClient, projeto_id: str) -> None:
    anotacao = _criar(client, projeto_id, titulo="Senhas", texto="Wi-Fi", cor="roxo", fixada=True)

    assert (anotacao["titulo"], anotacao["cor"], anotacao["fixada"]) == ("Senhas", "roxo", True)


@pytest.mark.parametrize(
    ("dados", "campos"),
    [
        ({}, {"texto": "Campo obrigatório."}),
        ({"texto": "   "}, {"texto": "Escreva o texto da anotação."}),
        ({"texto": "x" * 10001}, {"texto": "Use no máximo 10000 caracteres."}),
        ({"texto": "ok", "titulo": "t" * 121}, {"titulo": "Use no máximo 120 caracteres."}),
        ({"texto": "ok", "cor": "laranja"}, {"cor": "Valor não permitido."}),
    ],
)
def test_rn80_validacao(
    client: TestClient, projeto_id: str, dados: dict[str, object], campos: dict[str, str]
) -> None:
    resposta = client.post(f"/api/projetos/{projeto_id}/anotacoes", json=dados)

    assert _campos_invalidos(resposta) == campos


def test_rn80_texto_de_10000_caracteres_e_aceito(client: TestClient, projeto_id: str) -> None:
    assert len(_criar(client, projeto_id, texto="x" * 10000)["texto"]) == 10000


def test_atualizar_so_os_campos_enviados(
    client: TestClient, relogio: ClockFixo, projeto_id: str
) -> None:
    anotacao = _criar(client, projeto_id, titulo="Antigo", cor="azul")
    relogio.definir(date(2026, 10, 15))

    resposta = client.patch(f"/api/anotacoes/{anotacao['id']}", json={"texto": "Novo texto"})

    assert resposta.status_code == 200, resposta.text
    assert resposta.json() == {
        **anotacao,
        "texto": "Novo texto",
        "atualizado_em": "2026-10-15T15:00:00Z",
    }


@pytest.mark.parametrize("campo", ["titulo", "texto", "cor", "fixada"])
def test_atualizar_com_nulo_da_422(client: TestClient, projeto_id: str, campo: str) -> None:
    anotacao = _criar(client, projeto_id)

    resposta = client.patch(f"/api/anotacoes/{anotacao['id']}", json={campo: None})

    assert _campos_invalidos(resposta) == {campo: "Campo obrigatório."}


# RN-81


def test_rn81_fixadas_primeiro_e_mais_recentes_no_topo(
    client: TestClient, relogio: ClockFixo, projeto_id: str
) -> None:
    _criar(client, projeto_id, titulo="Velha")
    relogio.definir(date(2026, 10, 15))
    _criar(client, projeto_id, titulo="Fixada velha", fixada=True)
    relogio.definir(date(2026, 10, 16))
    _criar(client, projeto_id, titulo="Nova")
    relogio.definir(date(2026, 10, 17))
    _criar(client, projeto_id, titulo="Fixada nova", fixada=True)

    titulos = [a["titulo"] for a in _lista(client, projeto_id)]

    assert titulos == ["Fixada nova", "Fixada velha", "Nova", "Velha"]


def test_rn81_fixar_e_editar_contam_como_alteracao(
    client: TestClient, relogio: ClockFixo, projeto_id: str
) -> None:
    velha = _criar(client, projeto_id, titulo="Velha")
    relogio.definir(date(2026, 10, 15))
    _criar(client, projeto_id, titulo="Fixada", fixada=True)
    relogio.definir(date(2026, 10, 16))
    nova = _criar(client, projeto_id, titulo="Nova")

    relogio.definir(date(2026, 10, 17))
    client.patch(f"/api/anotacoes/{velha['id']}", json={"fixada": True})
    assert [a["titulo"] for a in _lista(client, projeto_id)] == ["Velha", "Fixada", "Nova"]

    relogio.definir(date(2026, 10, 18))
    client.patch(f"/api/anotacoes/{velha['id']}", json={"fixada": False})
    client.patch(f"/api/anotacoes/{nova['id']}", json={"cor": "verde"})
    assert [a["titulo"] for a in _lista(client, projeto_id)] == ["Fixada", "Nova", "Velha"]


# RN-90, RN-91


def test_rn90_excluir_manda_para_a_lixeira_e_restaurar_volta(
    client: TestClient, projeto_id: str
) -> None:
    anotacao = _criar(client, projeto_id)
    url = f"/api/anotacoes/{anotacao['id']}"

    assert client.delete(url).status_code == 204

    assert _lista(client, projeto_id) == []
    assert client.patch(url, json={"texto": "x"}).status_code == 404
    assert client.delete(url).status_code == 404
    restaurar = client.post(f"/api/lixeira/anotacao/{anotacao['id']}/restaurar")
    assert restaurar.status_code == 204
    assert _lista(client, projeto_id) == [anotacao]


def test_rn91_anotacoes_de_projeto_excluido_somem(client: TestClient, projeto_id: str) -> None:
    anotacao = _criar(client, projeto_id)
    client.delete(f"/api/projetos/{projeto_id}")

    assert client.get(f"/api/projetos/{projeto_id}/anotacoes").status_code == 404
    assert client.patch(f"/api/anotacoes/{anotacao['id']}", json={"texto": "x"}).status_code == 404
    assert (
        client.post(f"/api/projetos/{projeto_id}/anotacoes", json={"texto": "x"}).status_code == 404
    )


def test_projeto_inexistente_da_404(client: TestClient) -> None:
    resposta = client.get(f"/api/projetos/{uuid.uuid4()}/anotacoes")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["mensagem"] == "Projeto não encontrado."
