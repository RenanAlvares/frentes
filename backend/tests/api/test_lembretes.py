"""Lembretes: RN-40..46 na API. 07 §3.4; hoje = 2026-10-14 (quarta)."""

from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from app.clock import ClockFixo
from app.models import Configuracao
from tests.conftest import criar_lembrete, criar_projeto

SEGUNDA = {"frequencia": "semanal", "dias_semana": [0]}


@pytest.fixture
def projeto_id(client: TestClient) -> str:
    return str(criar_projeto(client, nome="Casa")["id"])


def _lista(client: TestClient, projeto_id: str) -> dict[str, Any]:
    resposta = client.get(f"/api/projetos/{projeto_id}/lembretes")
    assert resposta.status_code == 200, resposta.text
    lista: dict[str, Any] = resposta.json()
    return lista


def _titulos(lembretes: list[dict[str, Any]]) -> list[str]:
    return [lembrete["titulo"] for lembrete in lembretes]


def _campos_invalidos(resposta: Any) -> dict[str, str]:
    assert resposta.status_code == 422, resposta.text
    campos: dict[str, str] = resposta.json()["erro"]["campos"]
    return campos


# RN-40: campos e padrões


def test_rn40_criar_com_padroes(client: TestClient, projeto_id: str) -> None:
    lembrete = criar_lembrete(client, projeto_id, titulo="  Pagar IPTU  ", vencimento="2026-10-16")

    assert lembrete == {
        "id": lembrete["id"],
        "projeto_id": projeto_id,
        "titulo": "Pagar IPTU",
        "observacao": "",
        "vencimento": "2026-10-16",
        # Padrão da configuração antecedencia_padrao_lembretes (RN-100).
        "antecedencia_dias": 3,
        "recorrencia": None,
        "recorrencia_descricao": None,
        "dias_restantes": 2,
        "na_janela": True,
        "ocorrencias_atrasadas": 0,
        "concluido_em": None,
        "criado_em": "2026-10-14T15:00:00Z",
        "atualizado_em": "2026-10-14T15:00:00Z",
    }


def test_rn40_antecedencia_padrao_vem_da_configuracao(
    client: TestClient, app: FastAPI, projeto_id: str
) -> None:
    session_local: sessionmaker[Session] = app.state.session_local
    with session_local() as sessao:
        sessao.execute(
            update(Configuracao)
            .where(Configuracao.chave == "antecedencia_padrao_lembretes")
            .values(valor=7)
        )
        sessao.commit()

    assert criar_lembrete(client, projeto_id)["antecedencia_dias"] == 7
    assert criar_lembrete(client, projeto_id, antecedencia_dias=0)["antecedencia_dias"] == 0


@pytest.mark.parametrize(
    ("corpo", "campos"),
    [
        ({"vencimento": "2026-10-20"}, {"titulo": "Campo obrigatório."}),
        (
            {"titulo": "   ", "vencimento": "2026-10-20"},
            {"titulo": "Informe o título do lembrete."},
        ),
        ({"titulo": "A"}, {"vencimento": "Campo obrigatório."}),
        (
            {"titulo": "A", "vencimento": "2026-10-20", "observacao": "x" * 2001},
            {"observacao": "Use no máximo 2000 caracteres."},
        ),
        (
            {"titulo": "A", "vencimento": "2026-10-20", "antecedencia_dias": 61},
            {"antecedencia_dias": "Informe um valor menor ou igual a 60."},
        ),
        (
            {"titulo": "A", "vencimento": "2026-10-20", "recorrencia": {"frequencia": "mensal"}},
            {"recorrencia.dia_mes": "Informe o dia do mês."},
        ),
    ],
)
def test_rn40_criar_invalido(
    client: TestClient, projeto_id: str, corpo: dict[str, object], campos: dict[str, str]
) -> None:
    resposta = client.post(f"/api/projetos/{projeto_id}/lembretes", json=corpo)

    assert _campos_invalidos(resposta) == campos


# RN-42 e RN-45: janela, dias restantes e ordem


@pytest.mark.parametrize(
    ("vencimento", "antecedencia", "dias", "na_janela", "atrasadas"),
    [
        ("2026-10-16", 3, 2, True, 0),  # sexta, antecedência 3 → desde 13/10
        ("2026-10-17", 3, 3, True, 0),  # janela começa hoje
        ("2026-10-18", 3, 4, False, 0),
        ("2026-10-14", 0, 0, True, 1),  # vence hoje
        ("2026-10-10", 3, -4, True, 1),  # vencido: continua nos avisos até a baixa
    ],
)
def test_rn42_rn03_janela_e_dias_restantes(
    client: TestClient,
    projeto_id: str,
    vencimento: str,
    antecedencia: int,
    dias: int,
    na_janela: bool,
    atrasadas: int,
) -> None:
    lembrete = criar_lembrete(
        client, projeto_id, vencimento=vencimento, antecedencia_dias=antecedencia
    )

    assert lembrete["dias_restantes"] == dias
    assert lembrete["na_janela"] is na_janela
    assert lembrete["ocorrencias_atrasadas"] == atrasadas


def test_rn34_recorrente_atrasado_conta_as_ocorrencias(client: TestClient, projeto_id: str) -> None:
    mensal = {"frequencia": "mensal", "dia_mes": 5}

    lembrete = criar_lembrete(client, projeto_id, vencimento="2026-08-05", recorrencia=mensal)

    assert lembrete["ocorrencias_atrasadas"] == 3
    assert lembrete["recorrencia_descricao"] == "todo dia 5"


def test_rn45_ativos_por_vencimento(client: TestClient, projeto_id: str) -> None:
    for titulo, vencimento in [("C", "2026-11-01"), ("A", "2026-10-01"), ("B", "2026-10-20")]:
        criar_lembrete(client, projeto_id, titulo=titulo, vencimento=vencimento)

    lista = _lista(client, projeto_id)

    assert _titulos(lista["ativos"]) == ["A", "B", "C"]
    assert lista["concluidos"] == []


def test_rn41_projeto_arquivado_tira_da_janela(client: TestClient, projeto_id: str) -> None:
    criar_lembrete(client, projeto_id, vencimento="2026-10-10")

    client.patch(f"/api/projetos/{projeto_id}", json={"status": "concluido"})

    (lembrete,) = _lista(client, projeto_id)["ativos"]
    assert lembrete["na_janela"] is False


# RN-43 e RN-44: baixa e desfazer


def test_rn43_baixa_nao_recorrente_conclui_e_vai_para_concluidos(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    lembrete = criar_lembrete(client, projeto_id, titulo="IPTU", vencimento="2026-10-16")
    relogio.definir(date(2026, 10, 15))

    resposta = client.post(f"/api/lembretes/{lembrete['id']}/baixa")

    assert resposta.status_code == 200
    assert resposta.json()["concluido_em"] == "2026-10-15T15:00:00Z"
    assert resposta.json()["na_janela"] is False
    lista = _lista(client, projeto_id)
    assert lista["ativos"] == []
    assert _titulos(lista["concluidos"]) == ["IPTU"]


def test_baixa_em_lembrete_ja_concluido_da_409(client: TestClient, projeto_id: str) -> None:
    lembrete = criar_lembrete(client, projeto_id)
    client.post(f"/api/lembretes/{lembrete['id']}/baixa")

    resposta = client.post(f"/api/lembretes/{lembrete['id']}/baixa")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["mensagem"] == "O lembrete já recebeu baixa."


@pytest.mark.parametrize(
    ("vencimento", "proximo"),
    [
        ("2026-10-12", "2026-10-19"),  # vencido segunda: vai para a próxima segunda futura
        ("2026-10-26", "2026-11-02"),  # antes da janela: avança para a seguinte
    ],
    ids=["vencido", "antes-da-janela"],
)
def test_rn43_baixa_recorrente_registra_e_avanca(
    client: TestClient, projeto_id: str, vencimento: str, proximo: str
) -> None:
    lembrete = criar_lembrete(client, projeto_id, vencimento=vencimento, recorrencia=SEGUNDA)

    resposta = client.post(f"/api/lembretes/{lembrete['id']}/baixa").json()

    assert resposta["vencimento"] == proximo
    assert resposta["concluido_em"] is None
    assert _titulos(_lista(client, projeto_id)["ativos"]) == ["Lembrete"]


def test_rn44_desfazer_nao_recorrente_restaura_exatamente(
    client: TestClient, projeto_id: str
) -> None:
    lembrete = criar_lembrete(client, projeto_id, vencimento="2026-10-16")
    client.post(f"/api/lembretes/{lembrete['id']}/baixa")

    resposta = client.post(f"/api/lembretes/{lembrete['id']}/desfazer-baixa")

    assert resposta.status_code == 200
    assert resposta.json() == lembrete
    assert _lista(client, projeto_id)["concluidos"] == []


def test_rn44_desfazer_recorrente_restaura_cada_ocorrencia(
    client: TestClient, projeto_id: str, relogio: ClockFixo
) -> None:
    lembrete = criar_lembrete(client, projeto_id, vencimento="2026-10-12", recorrencia=SEGUNDA)
    url = f"/api/lembretes/{lembrete['id']}"
    client.post(f"{url}/baixa")  # 12/10 → 19/10
    relogio.definir(date(2026, 10, 19))
    client.post(f"{url}/baixa")  # 19/10 → 26/10
    relogio.definir(date(2026, 10, 14))

    assert client.post(f"{url}/desfazer-baixa").json()["vencimento"] == "2026-10-19"
    voltou = client.post(f"{url}/desfazer-baixa").json()

    assert voltou == {**lembrete, "atualizado_em": voltou["atualizado_em"]}
    assert client.post(f"{url}/desfazer-baixa").status_code == 409


def test_rn44_desfazer_sem_baixa_da_409(client: TestClient, projeto_id: str) -> None:
    lembrete = criar_lembrete(client, projeto_id)

    resposta = client.post(f"/api/lembretes/{lembrete['id']}/desfazer-baixa")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["mensagem"] == "Não há baixa para desfazer."


# Edição (RN-46) e exclusão (RN-90/91)


def test_rn46_editar_vencimento_muda_a_ancora(client: TestClient, projeto_id: str) -> None:
    lembrete = criar_lembrete(client, projeto_id, vencimento="2026-10-12", recorrencia=SEGUNDA)
    url = f"/api/lembretes/{lembrete['id']}"

    client.patch(url, json={"vencimento": "2026-10-28"})  # uma quarta, fora da regra (RN-33)
    resposta = client.post(f"{url}/baixa").json()

    assert resposta["vencimento"] == "2026-11-02"


def test_editar_campos_e_remover_a_repeticao(client: TestClient, projeto_id: str) -> None:
    lembrete = criar_lembrete(client, projeto_id, recorrencia=SEGUNDA)

    resposta = client.patch(
        f"/api/lembretes/{lembrete['id']}",
        json={"titulo": "Novo", "observacao": "Obs", "antecedencia_dias": 10, "recorrencia": None},
    ).json()

    assert resposta["titulo"] == "Novo"
    assert resposta["observacao"] == "Obs"
    assert resposta["antecedencia_dias"] == 10
    assert resposta["recorrencia"] is None
    assert resposta["recorrencia_descricao"] is None


def test_concluido_que_ganha_repeticao_volta_a_ficar_ativo(
    client: TestClient, projeto_id: str
) -> None:
    lembrete = criar_lembrete(client, projeto_id, titulo="Volta")
    client.post(f"/api/lembretes/{lembrete['id']}/baixa")

    resposta = client.patch(f"/api/lembretes/{lembrete['id']}", json={"recorrencia": SEGUNDA})

    assert resposta.json()["concluido_em"] is None
    lista = _lista(client, projeto_id)
    assert _titulos(lista["ativos"]) == ["Volta"]
    assert lista["concluidos"] == []


@pytest.mark.parametrize("campo", ["titulo", "observacao", "vencimento", "antecedencia_dias"])
def test_atualizar_nao_aceita_nulo_em_campo_obrigatorio(
    client: TestClient, projeto_id: str, campo: str
) -> None:
    lembrete = criar_lembrete(client, projeto_id)

    resposta = client.patch(f"/api/lembretes/{lembrete['id']}", json={campo: None})

    assert _campos_invalidos(resposta) == {campo: "Campo obrigatório."}


def test_rn90_excluir_e_restaurar(client: TestClient, projeto_id: str) -> None:
    lembrete = criar_lembrete(client, projeto_id)
    url = f"/api/lembretes/{lembrete['id']}"

    assert client.delete(url).status_code == 204
    assert _lista(client, projeto_id)["ativos"] == []
    for resposta in (client.patch(url, json={"titulo": "X"}), client.post(f"{url}/baixa")):
        assert resposta.status_code == 404
        assert resposta.json()["erro"]["mensagem"] == "Lembrete não encontrado."

    restaurar = client.post(f"/api/lixeira/lembrete/{lembrete['id']}/restaurar")
    assert restaurar.status_code == 204
    assert _titulos(_lista(client, projeto_id)["ativos"]) == ["Lembrete"]


def test_rn91_lembretes_de_projeto_excluido_ficam_ocultos(
    client: TestClient, projeto_id: str
) -> None:
    lembrete = criar_lembrete(client, projeto_id)
    client.delete(f"/api/lembretes/{lembrete['id']}")
    client.delete(f"/api/projetos/{projeto_id}")

    assert client.get(f"/api/projetos/{projeto_id}/lembretes").status_code == 404
    assert client.post(f"/api/lixeira/lembrete/{lembrete['id']}/restaurar").status_code == 404
