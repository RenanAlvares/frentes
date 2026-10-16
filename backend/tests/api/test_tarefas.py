"""Tarefas simples: quadro, CRUD, mover, concluir e desfazer. 07 §3.3 (simples)."""

import uuid
from datetime import date, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.clock import ClockFixo
from app.models import Tarefa
from tests.conftest import criar_projeto, criar_tarefa


@pytest.fixture
def projeto_id(client: TestClient) -> str:
    return str(criar_projeto(client, nome="Casa")["id"])


def _quadro(client: TestClient, projeto_id: str) -> dict[str, Any]:
    resposta = client.get(f"/api/projetos/{projeto_id}/tarefas")
    assert resposta.status_code == 200, resposta.text
    quadro: dict[str, Any] = resposta.json()
    return quadro


def _titulos(quadro: dict[str, Any], coluna: str) -> list[str]:
    return [tarefa["titulo"] for tarefa in quadro[coluna]]


def _posicoes(quadro: dict[str, Any], coluna: str) -> list[int]:
    return [tarefa["posicao"] for tarefa in quadro[coluna]]


def _mover(client: TestClient, tarefa: dict[str, Any], status: str, indice: int) -> Any:
    return client.post(
        f"/api/tarefas/{tarefa['id']}/mover", json={"status": status, "indice": indice}
    )


def _campos_invalidos(resposta: Any) -> dict[str, str]:
    assert resposta.status_code == 422, resposta.text
    campos: dict[str, str] = resposta.json()["erro"]["campos"]
    return campos


# Criar e ler (RN-20, RN-25)


def test_rn20_criar_com_padroes(client: TestClient, projeto_id: str) -> None:
    tarefa = criar_tarefa(client, projeto_id, titulo="  Comprar tinta  ")

    assert tarefa == {
        "id": tarefa["id"],
        "projeto_id": projeto_id,
        "titulo": "Comprar tinta",
        "descricao": "",
        "status": "pendente",
        "prioridade": "media",
        "tipo": "simples",
        "prazo": None,
        "recorrencia": None,
        "recorrencia_descricao": None,
        "meta_mensal": None,
        "progresso_mes": None,
        "posicao": 0,
        "concluida_em": None,
        "atrasada": False,
        "criado_em": "2026-10-14T15:00:00Z",
        "atualizado_em": "2026-10-14T15:00:00Z",
    }


def test_rn20_descricao_preserva_quebras_de_linha(client: TestClient, projeto_id: str) -> None:
    tarefa = criar_tarefa(client, projeto_id, descricao="linha 1\n\nlinha 2", prioridade="alta")

    detalhe = client.get(f"/api/tarefas/{tarefa['id']}").json()

    assert detalhe["descricao"] == "linha 1\n\nlinha 2"
    assert detalhe["prioridade"] == "alta"
    assert detalhe["execucoes"] == []


@pytest.mark.parametrize(
    ("corpo", "campos"),
    [
        ({}, {"titulo": "Campo obrigatório."}),
        ({"titulo": "   "}, {"titulo": "Informe o título da tarefa."}),
        ({"titulo": "x" * 201}, {"titulo": "Use no máximo 200 caracteres."}),
        ({"titulo": "A", "descricao": "x" * 5001}, {"descricao": "Use no máximo 5000 caracteres."}),
        ({"titulo": "A", "prioridade": "urgente"}, {"prioridade": "Valor não permitido."}),
        ({"titulo": "A", "prazo": "amanhã"}, {"prazo": "Informe uma data válida (AAAA-MM-DD)."}),
    ],
)
def test_rn20_criar_invalido(
    client: TestClient, projeto_id: str, corpo: dict[str, object], campos: dict[str, str]
) -> None:
    resposta = client.post(f"/api/projetos/{projeto_id}/tarefas", json=corpo)

    assert _campos_invalidos(resposta) == campos


def test_rn25_nova_tarefa_entra_no_topo_de_pendente(client: TestClient, projeto_id: str) -> None:
    for titulo in ("A", "B", "C"):
        criar_tarefa(client, projeto_id, titulo=titulo)

    quadro = _quadro(client, projeto_id)

    assert _titulos(quadro, "pendente") == ["C", "B", "A"]
    assert quadro["em_andamento"] == []
    assert quadro["concluida"] == []
    assert quadro["total_concluidas"] == 0


def test_rn121_busca_gravada(client: TestClient, app: FastAPI, projeto_id: str) -> None:
    tarefa = criar_tarefa(client, projeto_id, titulo="Pintar Sala", descricao="Cor: Pêssego")

    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        gravada = sessao.get(Tarefa, uuid.UUID(tarefa["id"]))
        assert gravada is not None
        assert gravada.busca == "pintar sala cor: pessego"


# RN-21: tipo e campos


def test_rn21_por_enquanto_so_tipo_simples(client: TestClient, projeto_id: str) -> None:
    resposta = client.post(
        f"/api/projetos/{projeto_id}/tarefas", json={"titulo": "A", "tipo": "repetida"}
    )

    assert _campos_invalidos(resposta) == {"tipo": "Valor não permitido."}


@pytest.mark.parametrize(
    ("extra", "campos"),
    [
        (
            {"recorrencia": {"frequencia": "diaria", "intervalo": 1}},
            {"recorrencia": "Tarefa simples não tem repetição."},
        ),
        ({"meta_mensal": 4}, {"meta_mensal": "Tarefa simples não tem meta mensal."}),
    ],
)
def test_rn21_simples_nao_tem_recorrencia_nem_meta(
    client: TestClient, projeto_id: str, extra: dict[str, object], campos: dict[str, str]
) -> None:
    criar = client.post(f"/api/projetos/{projeto_id}/tarefas", json={"titulo": "A", **extra})
    tarefa = criar_tarefa(client, projeto_id)
    editar = client.patch(f"/api/tarefas/{tarefa['id']}", json=extra)

    assert _campos_invalidos(criar) == campos
    assert _campos_invalidos(editar) == campos


def _tarefa_no_banco(projeto_id: str, **campos: object) -> Tarefa:
    agora = datetime(2026, 10, 14, 15, tzinfo=ClockFixo(date(2026, 10, 14)).agora_utc().tzinfo)
    padrao: dict[str, object] = {
        "projeto_id": uuid.UUID(projeto_id),
        "titulo": "X",
        "descricao": "",
        "status": "pendente",
        "prioridade": "media",
        "tipo": "simples",
        "prazo": None,
        "recorrencia": None,
        "meta_mensal": None,
        "posicao": 0,
        "busca": "x",
        "criado_em": agora,
        "atualizado_em": agora,
    }
    return Tarefa(**{**padrao, **campos})


RECORRENCIA = {"frequencia": "diaria", "intervalo": 1}


@pytest.mark.parametrize(
    "campos",
    [
        pytest.param({"tipo": "simples", "recorrencia": RECORRENCIA}, id="simples-com-recorrencia"),
        pytest.param({"tipo": "simples", "meta_mensal": 3}, id="simples-com-meta"),
        pytest.param({"tipo": "repetida", "recorrencia": RECORRENCIA}, id="repetida-sem-prazo"),
        pytest.param({"tipo": "repetida", "prazo": date(2026, 10, 20)}, id="repetida-sem-regra"),
        pytest.param(
            {
                "tipo": "repetida",
                "prazo": date(2026, 10, 20),
                "recorrencia": RECORRENCIA,
                "meta_mensal": 2,
            },
            id="repetida-com-meta",
        ),
        pytest.param({"tipo": "meta_mensal"}, id="meta-sem-valor"),
        pytest.param({"tipo": "meta_mensal", "meta_mensal": 0}, id="meta-zero"),
        pytest.param({"tipo": "meta_mensal", "meta_mensal": 32}, id="meta-32"),
        pytest.param(
            {"tipo": "meta_mensal", "meta_mensal": 4, "prazo": date(2026, 10, 20)},
            id="meta-com-prazo",
        ),
    ],
)
def test_rn21_check_do_banco_rejeita(
    client: TestClient, app: FastAPI, projeto_id: str, campos: dict[str, object]
) -> None:
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        sessao.add(_tarefa_no_banco(projeto_id, **campos))
        with pytest.raises(IntegrityError, match="ck_tarefas_tipo_campos"):
            sessao.commit()


@pytest.mark.parametrize(
    "campos",
    [
        pytest.param({"tipo": "simples", "prazo": date(2026, 10, 20)}, id="simples"),
        pytest.param(
            {"tipo": "repetida", "prazo": date(2026, 10, 20), "recorrencia": RECORRENCIA},
            id="repetida",
        ),
        pytest.param({"tipo": "meta_mensal", "meta_mensal": 31}, id="meta"),
    ],
)
def test_rn21_check_do_banco_aceita_combinacoes_validas(
    client: TestClient, app: FastAPI, projeto_id: str, campos: dict[str, object]
) -> None:
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        sessao.add(_tarefa_no_banco(projeto_id, **campos))
        sessao.commit()


# RN-22: concluir e sair de Concluída


def test_rn22_concluir_grava_concluida_em(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    tarefa = criar_tarefa(client, projeto_id)
    relogio.definir(date(2026, 10, 15))

    concluida = client.post(f"/api/tarefas/{tarefa['id']}/concluir").json()

    assert concluida["status"] == "concluida"
    assert concluida["concluida_em"] == "2026-10-15T15:00:00Z"
    quadro = _quadro(client, projeto_id)
    assert quadro["pendente"] == []
    assert _titulos(quadro, "concluida") == ["Tarefa"]
    assert quadro["total_concluidas"] == 1


def test_concluir_tarefa_ja_concluida_da_409(client: TestClient, projeto_id: str) -> None:
    tarefa = criar_tarefa(client, projeto_id)
    client.post(f"/api/tarefas/{tarefa['id']}/concluir")

    resposta = client.post(f"/api/tarefas/{tarefa['id']}/concluir")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["mensagem"] == "A tarefa já está concluída."


def test_rn22_mover_de_volta_limpa_concluida_em(client: TestClient, projeto_id: str) -> None:
    tarefa = criar_tarefa(client, projeto_id)
    client.post(f"/api/tarefas/{tarefa['id']}/concluir")

    quadro = _mover(client, tarefa, "em_andamento", 0).json()

    (movida,) = quadro["em_andamento"]
    assert movida["status"] == "em_andamento"
    assert movida["concluida_em"] is None
    assert quadro["total_concluidas"] == 0


@pytest.mark.parametrize("pelo", ["patch", "mover"])
def test_rn22_mover_para_concluida_grava_concluida_em(
    client: TestClient, projeto_id: str, pelo: str
) -> None:
    tarefa = criar_tarefa(client, projeto_id)

    if pelo == "patch":
        client.patch(f"/api/tarefas/{tarefa['id']}", json={"status": "concluida"})
    else:
        _mover(client, tarefa, "concluida", 5)

    (concluida,) = _quadro(client, projeto_id)["concluida"]
    assert concluida["concluida_em"] == "2026-10-14T15:00:00Z"


def test_patch_status_poe_no_topo_da_nova_coluna(client: TestClient, projeto_id: str) -> None:
    a, b, c = (criar_tarefa(client, projeto_id, titulo=t) for t in ("A", "B", "C"))
    _mover(client, a, "em_andamento", 0)
    _mover(client, b, "em_andamento", 1)

    resposta = client.patch(f"/api/tarefas/{c['id']}", json={"status": "em_andamento"})

    assert resposta.status_code == 200
    quadro = _quadro(client, projeto_id)
    assert _titulos(quadro, "em_andamento") == ["C", "A", "B"]
    assert _posicoes(quadro, "em_andamento") == [0, 1, 2]
    assert quadro["pendente"] == []


def test_atualizar_campos_sem_mudar_de_coluna(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    tarefa = criar_tarefa(client, projeto_id, prazo="2026-10-30")
    relogio.definir(date(2026, 10, 20))

    resposta = client.patch(
        f"/api/tarefas/{tarefa['id']}",
        json={"titulo": "Nova", "prazo": None, "prioridade": "baixa"},
    )

    assert resposta.json() == {
        **tarefa,
        "titulo": "Nova",
        "prazo": None,
        "prioridade": "baixa",
        "atualizado_em": "2026-10-20T15:00:00Z",
    }


@pytest.mark.parametrize("campo", ["titulo", "descricao", "prioridade", "status", "tipo"])
def test_atualizar_nao_aceita_nulo_em_campo_obrigatorio(
    client: TestClient, projeto_id: str, campo: str
) -> None:
    tarefa = criar_tarefa(client, projeto_id)

    resposta = client.patch(f"/api/tarefas/{tarefa['id']}", json={campo: None})

    assert _campos_invalidos(resposta) == {campo: "Campo obrigatório."}


# RN-25: mover e ordem


@pytest.fixture
def quatro(client: TestClient, projeto_id: str) -> dict[str, dict[str, Any]]:
    """Pendente = [A, B, C, D] (criadas de trás para frente, pois a nova entra no topo)."""
    tarefas = {t: criar_tarefa(client, projeto_id, titulo=t) for t in ("D", "C", "B", "A")}
    assert _titulos(_quadro(client, projeto_id), "pendente") == ["A", "B", "C", "D"]
    return tarefas


@pytest.mark.parametrize(
    ("indice", "esperado"),
    [(0, ["X", "A", "B"]), (1, ["A", "X", "B"]), (2, ["A", "B", "X"]), (99, ["A", "B", "X"])],
    ids=["topo", "meio", "fim", "alem-do-fim"],
)
def test_rn25_mover_para_outra_coluna_renumera_as_duas(
    client: TestClient,
    projeto_id: str,
    quatro: dict[str, dict[str, Any]],
    indice: int,
    esperado: list[str],
) -> None:
    for titulo in ("A", "B"):
        _mover(client, quatro[titulo], "em_andamento", 99)
    client.patch(f"/api/tarefas/{quatro['C']['id']}", json={"titulo": "X"})

    quadro = _mover(client, quatro["C"], "em_andamento", indice).json()

    assert _titulos(quadro, "em_andamento") == esperado
    assert _posicoes(quadro, "em_andamento") == [0, 1, 2]
    assert _titulos(quadro, "pendente") == ["D"]
    assert _posicoes(quadro, "pendente") == [0]


@pytest.mark.parametrize(
    ("titulo", "indice", "esperado"),
    [
        ("D", 0, ["D", "A", "B", "C"]),
        ("A", 2, ["B", "C", "A", "D"]),
        ("B", 99, ["A", "C", "D", "B"]),
    ],
)
def test_rn25_reordenar_dentro_da_coluna(
    client: TestClient,
    quatro: dict[str, dict[str, Any]],
    titulo: str,
    indice: int,
    esperado: list[str],
) -> None:
    quadro = _mover(client, quatro[titulo], "pendente", indice).json()

    assert _titulos(quadro, "pendente") == esperado
    assert _posicoes(quadro, "pendente") == [0, 1, 2, 3]


def test_rn25_indice_negativo_e_invalido(
    client: TestClient, quatro: dict[str, dict[str, Any]]
) -> None:
    resposta = _mover(client, quatro["A"], "pendente", -1)

    assert _campos_invalidos(resposta) == {"indice": "Informe um valor maior ou igual a 0."}


def test_rn25_concluida_ordenada_por_data_e_limitada_a_20(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    for dia in range(1, 23):
        tarefa = criar_tarefa(client, projeto_id, titulo=f"T{dia:02d}")
        relogio.definir(date(2026, 10, dia))
        client.post(f"/api/tarefas/{tarefa['id']}/concluir")

    quadro = _quadro(client, projeto_id)
    todas = client.get(f"/api/projetos/{projeto_id}/tarefas/concluidas").json()

    assert quadro["total_concluidas"] == 22
    assert _titulos(quadro, "concluida") == [f"T{dia:02d}" for dia in range(22, 2, -1)]
    assert [t["titulo"] for t in todas] == [f"T{dia:02d}" for dia in range(22, 0, -1)]


# RN-26: desfazer conclusão (simples)


def test_rn26_desfazer_volta_para_o_topo_de_pendente(client: TestClient, projeto_id: str) -> None:
    feita = criar_tarefa(client, projeto_id, titulo="Feita")
    criar_tarefa(client, projeto_id, titulo="Outra")
    client.post(f"/api/tarefas/{feita['id']}/concluir")

    resposta = client.post(f"/api/tarefas/{feita['id']}/desfazer-conclusao")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "pendente"
    assert resposta.json()["concluida_em"] is None
    quadro = _quadro(client, projeto_id)
    assert _titulos(quadro, "pendente") == ["Feita", "Outra"]
    assert _posicoes(quadro, "pendente") == [0, 1]


def test_rn26_desfazer_sem_conclusao_da_409(client: TestClient, projeto_id: str) -> None:
    tarefa = criar_tarefa(client, projeto_id)

    resposta = client.post(f"/api/tarefas/{tarefa['id']}/desfazer-conclusao")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["mensagem"] == "Não há conclusão para desfazer."


# RN-27: atrasada


@pytest.mark.parametrize(
    ("prazo", "concluir", "atrasada"),
    [
        ("2026-10-13", False, True),
        ("2026-10-14", False, False),
        ("2026-10-15", False, False),
        (None, False, False),
        ("2026-10-13", True, False),
    ],
    ids=["ontem", "hoje", "amanha", "sem-prazo", "concluida"],
)
def test_rn27_atrasada(
    client: TestClient, projeto_id: str, prazo: str | None, concluir: bool, atrasada: bool
) -> None:
    tarefa = criar_tarefa(client, projeto_id, prazo=prazo)
    if concluir:
        client.post(f"/api/tarefas/{tarefa['id']}/concluir")

    assert client.get(f"/api/tarefas/{tarefa['id']}").json()["atrasada"] is atrasada


def test_rn27_projeto_arquivado_nao_tem_atrasada(client: TestClient, projeto_id: str) -> None:
    tarefa = criar_tarefa(client, projeto_id, prazo="2026-10-01")

    client.patch(f"/api/projetos/{projeto_id}", json={"status": "concluido"})

    assert client.get(f"/api/tarefas/{tarefa['id']}").json()["atrasada"] is False


# RN-90 e RN-91: exclusão lógica


def test_rn90_excluir_tarefa(client: TestClient, projeto_id: str) -> None:
    tarefa = criar_tarefa(client, projeto_id, titulo="Some")
    criar_tarefa(client, projeto_id, titulo="Fica")
    url = f"/api/tarefas/{tarefa['id']}"

    assert client.delete(url).status_code == 204

    assert _titulos(_quadro(client, projeto_id), "pendente") == ["Fica"]
    for resposta in (
        client.get(url),
        client.patch(url, json={"titulo": "B"}),
        client.delete(url),
        client.post(f"{url}/concluir"),
        _mover(client, tarefa, "pendente", 0),
    ):
        assert resposta.status_code == 404
        assert resposta.json()["erro"]["mensagem"] == "Tarefa não encontrada."


def test_rn91_tarefas_de_projeto_excluido_ficam_ocultas(
    client: TestClient, projeto_id: str
) -> None:
    tarefa = criar_tarefa(client, projeto_id)

    client.delete(f"/api/projetos/{projeto_id}")

    assert client.get(f"/api/tarefas/{tarefa['id']}").status_code == 404
    resposta = client.get(f"/api/projetos/{projeto_id}/tarefas")
    assert resposta.status_code == 404
    assert resposta.json()["erro"]["mensagem"] == "Projeto não encontrado."


@pytest.mark.parametrize("rota", ["tarefas", "tarefas/concluidas"])
def test_projeto_inexistente(client: TestClient, rota: str) -> None:
    resposta = client.get(f"/api/projetos/{uuid.uuid4()}/{rota}")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["mensagem"] == "Projeto não encontrado."


def test_criar_em_projeto_inexistente(client: TestClient) -> None:
    resposta = client.post(f"/api/projetos/{uuid.uuid4()}/tarefas", json={"titulo": "A"})

    assert resposta.status_code == 404
