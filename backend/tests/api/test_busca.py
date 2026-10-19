"""Busca global: RN-120..121 na API."""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.clock import ClockFixo
from tests.conftest import criar_lembrete, criar_projeto, criar_tarefa


def _buscar(client: TestClient, q: str) -> dict[str, Any]:
    resposta = client.get("/api/busca", params={"q": q})
    assert resposta.status_code == 200, resposta.text
    resultado: dict[str, Any] = resposta.json()
    return resultado


def _titulos(client: TestClient, q: str) -> dict[str, list[str]]:
    return {tipo: [i["titulo"] for i in itens] for tipo, itens in _buscar(client, q).items()}


def _anotacao(client: TestClient, projeto_id: str, **campos: object) -> dict[str, Any]:
    resposta = client.post(f"/api/projetos/{projeto_id}/anotacoes", json=campos)
    assert resposta.status_code == 201, resposta.text
    anotacao: dict[str, Any] = resposta.json()
    return anotacao


def _documento(client: TestClient, projeto_id: str, nome: str) -> dict[str, Any]:
    resposta = client.post(
        f"/api/projetos/{projeto_id}/documentos", files=[("arquivos", (nome, b"x"))]
    )
    assert resposta.status_code == 201, resposta.text
    documento: dict[str, Any] = resposta.json()[0]
    return documento


VAZIO = {"projetos": [], "tarefas": [], "lembretes": [], "anotacoes": [], "documentos": []}


def test_rn120_busca_em_todos_os_campos_sem_acentos_nem_maiusculas(client: TestClient) -> None:
    casa = criar_projeto(client, nome="Reforma da Cozinha", cor="verde")
    pid = casa["id"]
    criar_projeto(client, nome="Viagem", descricao="Levar o fogão portátil")
    criar_tarefa(client, pid, titulo="Comprar azulejo da COZINHA")
    criar_tarefa(client, pid, titulo="Pintar", descricao="Teto da cozinha")
    criar_lembrete(client, pid, titulo="Gás", observacao="Revisar fogão da cozinha")
    _anotacao(client, pid, texto="Medidas: cozinha 3 x 4")
    _documento(client, pid, "Planta-Cozinha.pdf")
    criar_tarefa(client, pid, titulo="Não aparece")

    assert _titulos(client, "cozínha") == {
        "projetos": ["Reforma da Cozinha"],
        # Mesmo `atualizado_em` (relógio parado): empate pelo texto.
        "tarefas": ["Comprar azulejo da COZINHA", "Pintar"],
        "lembretes": ["Gás"],
        "anotacoes": ["Medidas: cozinha 3 x 4"],
        "documentos": ["Planta-Cozinha.pdf"],
    }
    assert _titulos(client, "FOGAO") == {
        **{tipo: [] for tipo in VAZIO},
        "projetos": ["Viagem"],
        "lembretes": ["Gás"],
    }


def test_formato_do_item(client: TestClient) -> None:
    projeto = criar_projeto(client, nome="Casa", cor="roxo")
    tarefa = criar_tarefa(client, projeto["id"], titulo="Trocar lâmpada")

    resultado = _buscar(client, "lampada")

    assert resultado["tarefas"] == [
        {
            "id": tarefa["id"],
            "titulo": "Trocar lâmpada",
            "projeto": {"id": projeto["id"], "nome": "Casa", "cor": "roxo"},
            "arquivado": False,
        }
    ]
    assert _buscar(client, "casa")["projetos"] == [
        {
            "id": projeto["id"],
            "titulo": "Casa",
            "projeto": {"id": projeto["id"], "nome": "Casa", "cor": "roxo"},
            "arquivado": False,
        }
    ]


def test_rn120_anotacao_sem_titulo_mostra_o_comeco_do_texto(
    client: TestClient, relogio: ClockFixo
) -> None:
    pid = criar_projeto(client)["id"]
    _anotacao(client, pid, titulo="Senhas", texto="wifi da casa")
    relogio.definir(date(2026, 10, 15))
    _anotacao(client, pid, texto="Senha do portão\nsegunda linha")

    assert _titulos(client, "senha")["anotacoes"] == ["Senha do portão", "Senhas"]


def test_rn90_rn91_excluidos_nao_aparecem(client: TestClient) -> None:
    ativo = criar_projeto(client, nome="Ativo")["id"]
    fica = criar_tarefa(client, ativo, titulo="Tinta fica")
    excluida = criar_tarefa(client, ativo, titulo="Tinta excluída")
    client.delete(f"/api/tarefas/{excluida['id']}")
    lixo = criar_projeto(client, nome="Tinta no lixo")["id"]
    criar_tarefa(client, lixo, titulo="Tinta de projeto excluído")
    client.delete(f"/api/projetos/{lixo}")

    resultado = _buscar(client, "tinta")

    assert resultado["projetos"] == []
    assert [t["id"] for t in resultado["tarefas"]] == [fica["id"]]


def test_rn120_projeto_arquivado_aparece_marcado(client: TestClient) -> None:
    arquivado = criar_projeto(client, nome="Mudança antiga")
    criar_tarefa(client, arquivado["id"], titulo="Caixas da mudança")
    client.patch(f"/api/projetos/{arquivado['id']}", json={"status": "concluido"})

    resultado = _buscar(client, "mudanca")

    assert [(p["titulo"], p["arquivado"]) for p in resultado["projetos"]] == [
        ("Mudança antiga", True)
    ]
    assert [(t["titulo"], t["arquivado"]) for t in resultado["tarefas"]] == [
        ("Caixas da mudança", True)
    ]


def test_rn121_ate_10_por_tipo_mais_recentes_primeiro(
    client: TestClient, relogio: ClockFixo
) -> None:
    pid = criar_projeto(client, nome="Projeto")["id"]
    tarefas = [criar_tarefa(client, pid, titulo=f"Item {n:02d}") for n in range(12)]
    # A primeira criada passa a ser a alteração mais recente.
    relogio.definir(date(2026, 10, 15))
    client.patch(f"/api/tarefas/{tarefas[0]['id']}", json={"titulo": "Item 00 editado"})

    titulos = _titulos(client, "item")["tarefas"]

    assert len(titulos) == 10
    assert titulos[0] == "Item 00 editado"


@pytest.mark.parametrize("curinga", ["%", "_", "a%b", "a_b"])
def test_rn121_curingas_do_like_sao_texto(client: TestClient, curinga: str) -> None:
    pid = criar_projeto(client, nome="Projeto")["id"]
    criar_tarefa(client, pid, titulo="Desconto de 10% em a_b")
    criar_tarefa(client, pid, titulo="Outra coisa qualquer")

    termo = curinga if len(curinga) > 1 else f"10{curinga}"
    titulos = _titulos(client, termo)["tarefas"]

    esperado = ["Desconto de 10% em a_b"] if termo in ("10%", "a_b") else []
    assert titulos == esperado


@pytest.mark.parametrize("q", ["", "a", "  á  ", "!"])
def test_rn121_minimo_de_2_caracteres(client: TestClient, q: str) -> None:
    resposta = client.get("/api/busca", params={"q": q})

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["campos"] == {"q": "Digite pelo menos 2 letras para buscar."}


def test_sem_resultados(client: TestClient) -> None:
    criar_projeto(client, nome="Casa")

    assert _buscar(client, "inexistente") == VAZIO
