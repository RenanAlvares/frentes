"""Projetos: CRUD, RN-10..16 e exclusão lógica (RN-90). 07 §3.5."""

import uuid
from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.clock import ClockFixo
from app.models import Projeto
from tests.conftest import criar_projeto

ORDEM_INVALIDA = "Envie todos os projetos ativos, cada um uma vez."


def _ids(client: TestClient, **params: object) -> list[str]:
    return [projeto["id"] for projeto in client.get("/api/projetos", params=params).json()]


def _campos_invalidos(resposta: Any) -> dict[str, str]:
    assert resposta.status_code == 422, resposta.text
    campos: dict[str, str] = resposta.json()["erro"]["campos"]
    return campos


def _busca_no_banco(app: FastAPI, projeto_id: str) -> str:
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        projeto = sessao.get(Projeto, uuid.UUID(projeto_id))
        assert projeto is not None
        return projeto.busca


# CRUD


def test_rn11_criar_com_padroes(client: TestClient) -> None:
    projeto = criar_projeto(client, nome="Reforma")

    assert projeto == {
        "id": projeto["id"],
        "nome": "Reforma",
        "descricao": "",
        "status": "em_andamento",
        "cor": "azul",
        "data_inicio": None,
        "prazo": None,
        "acompanhar_progresso": False,
        "progresso": None,
        "avisos": 0,
        "posicao": 0,
        "criado_em": "2026-10-14T15:00:00Z",
        "atualizado_em": "2026-10-14T15:00:00Z",
    }


def test_criar_com_todos_os_campos_e_obter(client: TestClient) -> None:
    criado = criar_projeto(
        client,
        nome="Site",
        descricao="Novo site",
        status="planejado",
        cor="roxo",
        data_inicio="2026-10-01",
        prazo="2026-12-20",
        acompanhar_progresso=True,
    )

    obtido = client.get(f"/api/projetos/{criado['id']}").json()

    assert obtido == criado
    assert obtido["progresso"] == {"concluidas": 0, "total": 0}


def test_atualizar_muda_so_os_campos_enviados(client: TestClient, relogio: ClockFixo) -> None:
    criado = criar_projeto(client, nome="Site", descricao="Antiga", prazo="2026-12-20")
    relogio.definir(date(2026, 10, 20))

    resposta = client.patch(
        f"/api/projetos/{criado['id']}", json={"descricao": "Nova", "prazo": None}
    )

    assert resposta.status_code == 200
    assert resposta.json() == {
        **criado,
        "descricao": "Nova",
        "prazo": None,
        "atualizado_em": "2026-10-20T15:00:00Z",
    }


def test_listar_devolve_resumo(client: TestClient) -> None:
    criar_projeto(client, nome="A", descricao="não aparece no resumo")

    (resumo,) = client.get("/api/projetos").json()

    assert set(resumo) == {
        "id",
        "nome",
        "status",
        "cor",
        "prazo",
        "acompanhar_progresso",
        "progresso",
        "avisos",
        "posicao",
    }


def test_rn121_busca_gravada_e_atualizada(client: TestClient, app: FastAPI) -> None:
    projeto = criar_projeto(client, nome="Reforma da  Cozinha", descricao="Orçamento")
    assert _busca_no_banco(app, projeto["id"]) == "reforma da cozinha orcamento"

    client.patch(f"/api/projetos/{projeto['id']}", json={"nome": "Elétrica"})

    assert _busca_no_banco(app, projeto["id"]) == "eletrica orcamento"


# RN-10 e RN-11: validação


def test_rn10_nome_sem_espacos_nas_pontas(client: TestClient) -> None:
    assert criar_projeto(client, nome="  Reforma  ")["nome"] == "Reforma"


@pytest.mark.parametrize(
    ("corpo", "campos"),
    [
        ({}, {"nome": "Campo obrigatório."}),
        ({"nome": "   "}, {"nome": "Informe o nome do projeto."}),
        ({"nome": "x" * 101}, {"nome": "Use no máximo 100 caracteres."}),
        ({"nome": "A", "descricao": "x" * 2001}, {"descricao": "Use no máximo 2000 caracteres."}),
        ({"nome": "A", "status": "pausado"}, {"status": "Valor não permitido."}),
        ({"nome": "A", "cor": "dourado"}, {"cor": "Valor não permitido."}),
        ({"nome": "A", "prazo": "31/12/2026"}, {"prazo": "Informe uma data válida (AAAA-MM-DD)."}),
    ],
)
def test_rn10_criar_invalido(
    client: TestClient, corpo: dict[str, object], campos: dict[str, str]
) -> None:
    assert _campos_invalidos(client.post("/api/projetos", json=corpo)) == campos


def test_rn10_nome_com_100_caracteres_depois_do_strip(client: TestClient) -> None:
    assert len(criar_projeto(client, nome=f"  {'x' * 100}  ")["nome"]) == 100


@pytest.mark.parametrize("campo", ["nome", "descricao", "status", "cor", "acompanhar_progresso"])
def test_rn10_atualizar_nao_aceita_nulo_em_campo_obrigatorio(
    client: TestClient, campo: str
) -> None:
    projeto = criar_projeto(client)

    resposta = client.patch(f"/api/projetos/{projeto['id']}", json={campo: None})

    assert _campos_invalidos(resposta) == {campo: "Campo obrigatório."}


# RN-12 (parcial): concluído = arquivado


def test_rn12_concluido_sai_da_home_e_aparece_em_arquivados(client: TestClient) -> None:
    ativo = criar_projeto(client, nome="Ativo")
    arquivado = criar_projeto(client, nome="Pronto")

    client.patch(f"/api/projetos/{arquivado['id']}", json={"status": "concluido"})

    assert _ids(client) == [ativo["id"]]
    assert _ids(client, arquivados="true") == [arquivado["id"]]


def test_rn12_reabrir_volta_para_a_home_na_posicao_antiga(client: TestClient) -> None:
    primeiro = criar_projeto(client, nome="Primeiro")
    segundo = criar_projeto(client, nome="Segundo")
    client.patch(f"/api/projetos/{primeiro['id']}", json={"status": "concluido"})

    client.patch(f"/api/projetos/{primeiro['id']}", json={"status": "em_andamento"})

    assert _ids(client) == [primeiro["id"], segundo["id"]]
    assert _ids(client, arquivados="true") == []


# RN-15: ordem


def test_rn15_novo_projeto_vai_para_o_fim(client: TestClient) -> None:
    ids = [criar_projeto(client, nome=nome)["id"] for nome in ("A", "B", "C")]

    assert _ids(client) == ids
    assert [p["posicao"] for p in client.get("/api/projetos").json()] == [0, 1, 2]


def test_rn15_reordenar_grava_as_posicoes(client: TestClient) -> None:
    a, b, c = (criar_projeto(client, nome=nome)["id"] for nome in ("A", "B", "C"))

    resposta = client.put("/api/projetos/ordem", json={"ids": [c, a, b]})

    assert resposta.status_code == 204
    assert _ids(client) == [c, a, b]
    assert [p["posicao"] for p in client.get("/api/projetos").json()] == [0, 1, 2]


def test_rn15_reordenar_ignora_arquivados(client: TestClient) -> None:
    a, b = (criar_projeto(client, nome=nome)["id"] for nome in ("A", "B"))
    arquivado = criar_projeto(client, nome="Arquivado", status="concluido")["id"]

    assert client.put("/api/projetos/ordem", json={"ids": [b, a]}).status_code == 204
    assert _ids(client) == [b, a]
    assert _ids(client, arquivados="true") == [arquivado]


@pytest.mark.parametrize(
    "lista",
    [
        pytest.param(lambda a, b, _x, _y: [a], id="faltando"),
        pytest.param(lambda a, b, x, _y: [a, b, x], id="sobrando-arquivado"),
        pytest.param(lambda a, b, _x, y: [a, b, y], id="sobrando-excluido"),
        pytest.param(lambda a, b, _x, _y: [a, b, str(uuid.uuid4())], id="sobrando-inexistente"),
        pytest.param(lambda a, b, _x, _y: [a, a, b], id="repetido"),
        pytest.param(lambda a, _b, _x, _y: [a, a], id="repetido-no-lugar-de-outro"),
    ],
)
def test_rn15_reordenar_exige_exatamente_os_ativos(client: TestClient, lista: Any) -> None:
    a, b = (criar_projeto(client, nome=nome)["id"] for nome in ("A", "B"))
    arquivado = criar_projeto(client, nome="X", status="concluido")["id"]
    excluido = criar_projeto(client, nome="Y")["id"]
    client.delete(f"/api/projetos/{excluido}")

    resposta = client.put("/api/projetos/ordem", json={"ids": lista(a, b, arquivado, excluido)})

    assert _campos_invalidos(resposta) == {"ids": ORDEM_INVALIDA}
    assert _ids(client) == [a, b]


# RN-16: datas


def test_rn16_inicio_depois_do_prazo_na_criacao(client: TestClient) -> None:
    resposta = client.post(
        "/api/projetos", json={"nome": "A", "data_inicio": "2026-11-02", "prazo": "2026-11-01"}
    )

    assert _campos_invalidos(resposta) == {"prazo": "O prazo não pode ser anterior ao início."}


def test_rn16_inicio_igual_ao_prazo_e_valido(client: TestClient) -> None:
    projeto = criar_projeto(client, data_inicio="2026-11-01", prazo="2026-11-01")

    assert projeto["data_inicio"] == projeto["prazo"] == "2026-11-01"


@pytest.mark.parametrize("alteracao", [{"prazo": "2026-10-31"}, {"data_inicio": "2026-12-02"}])
def test_rn16_atualizar_considera_a_data_ja_gravada(
    client: TestClient, alteracao: dict[str, str]
) -> None:
    projeto = criar_projeto(client, data_inicio="2026-11-01", prazo="2026-12-01")

    resposta = client.patch(f"/api/projetos/{projeto['id']}", json=alteracao)

    assert _campos_invalidos(resposta) == {"prazo": "O prazo não pode ser anterior ao início."}
    assert client.get(f"/api/projetos/{projeto['id']}").json() == projeto


def test_rn16_limpar_uma_das_datas_libera_a_outra(client: TestClient) -> None:
    projeto = criar_projeto(client, data_inicio="2026-11-01", prazo="2026-12-01")

    resposta = client.patch(
        f"/api/projetos/{projeto['id']}", json={"prazo": None, "data_inicio": "2027-01-01"}
    )

    assert resposta.status_code == 200


# RN-90: exclusão lógica


def test_rn90_excluir_tira_de_todas_as_rotas(client: TestClient, app: FastAPI) -> None:
    projeto = criar_projeto(client, nome="Some")
    url = f"/api/projetos/{projeto['id']}"

    assert client.delete(url).status_code == 204

    assert _ids(client) == []
    assert _ids(client, arquivados="true") == []
    for resposta in (client.get(url), client.patch(url, json={"nome": "B"}), client.delete(url)):
        assert resposta.status_code == 404
        assert resposta.json()["erro"] == {
            "codigo": "nao_encontrado",
            "mensagem": "Projeto não encontrado.",
        }
    # Continua no banco, marcado (vai para a Lixeira na fase 5).
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        gravado = sessao.get(Projeto, uuid.UUID(projeto["id"]))
        assert gravado is not None
        assert gravado.excluido_em is not None


def test_projeto_inexistente_e_id_invalido(client: TestClient) -> None:
    assert client.get(f"/api/projetos/{uuid.uuid4()}").status_code == 404
    assert _campos_invalidos(client.get("/api/projetos/abc")) == {
        "projeto_id": "Identificador inválido."
    }
