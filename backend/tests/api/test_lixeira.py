"""Lixeira: RN-90..94 na API (07 §3.6). Restaurar também é o Desfazer das exclusões."""

import logging
import sqlite3
import uuid
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.clock import ClockFixo
from app.config import Settings
from app.main import create_app
from app.storage.local import LocalStorage, get_storage
from tests.conftest import criar_lembrete, criar_projeto, criar_tarefa

TABELAS = (
    "projetos",
    "tarefas",
    "tarefa_execucoes",
    "lembretes",
    "lembrete_baixas",
    "documentos",
    "anotacoes",
)


def _lixeira(client: TestClient) -> list[Any]:
    resposta = client.get("/api/lixeira")
    assert resposta.status_code == 200, resposta.text
    itens: list[Any] = resposta.json()
    return itens


def _resumo(client: TestClient) -> list[tuple[str, str, str | None]]:
    return [(i["tipo"], i["titulo"], i["projeto_nome"]) for i in _lixeira(client)]


def _linhas(settings: Settings) -> dict[str, int]:
    with closing(sqlite3.connect(settings.data_dir / "frentes.db")) as conexao:
        return {t: conexao.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABELAS}


def _arquivos(settings: Settings) -> list[Path]:
    raiz = settings.pasta_anexos
    return [p for p in raiz.rglob("*") if p.is_file()] if raiz.exists() else []


def _documento(client: TestClient, projeto_id: str, nome: str = "a.pdf") -> dict[str, Any]:
    resposta = client.post(
        f"/api/projetos/{projeto_id}/documentos", files=[("arquivos", (nome, b"%PDF"))]
    )
    assert resposta.status_code == 201, resposta.text
    documento: dict[str, Any] = resposta.json()[0]
    return documento


def _anotacao(client: TestClient, projeto_id: str, **campos: object) -> dict[str, Any]:
    resposta = client.post(
        f"/api/projetos/{projeto_id}/anotacoes", json={"texto": "Texto", **campos}
    )
    assert resposta.status_code == 201, resposta.text
    anotacao: dict[str, Any] = resposta.json()
    return anotacao


def _projeto_completo(client: TestClient, nome: str) -> str:
    """Projeto com tarefa (e execução de meta), lembrete (e baixa), documento e anotação."""
    projeto_id = str(criar_projeto(client, nome=nome)["id"])
    meta = criar_tarefa(client, projeto_id, tipo="meta_mensal", meta_mensal=4)
    client.post(f"/api/tarefas/{meta['id']}/concluir")
    mensal = {"frequencia": "mensal", "dia_mes": 20}
    lembrete = criar_lembrete(client, projeto_id, recorrencia=mensal)
    client.post(f"/api/lembretes/{lembrete['id']}/baixa")
    _documento(client, projeto_id)
    _anotacao(client, projeto_id)
    return projeto_id


# RN-92: restaurar (também usado pelos Desfazer)


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


def test_rn92_restaurar_projeto_traz_os_itens_menos_os_excluidos_antes(
    client: TestClient,
) -> None:
    projeto_id = criar_projeto(client, nome="Casa")["id"]
    criar_tarefa(client, projeto_id, titulo="Volta")
    antes = criar_tarefa(client, projeto_id, titulo="Excluída antes")
    client.delete(f"/api/tarefas/{antes['id']}")
    client.delete(f"/api/projetos/{projeto_id}")
    assert _resumo(client) == [("projeto", "Casa", None)]

    client.post(f"/api/lixeira/projeto/{projeto_id}/restaurar")

    quadro = client.get(f"/api/projetos/{projeto_id}/tarefas").json()
    assert [t["titulo"] for t in quadro["pendente"]] == ["Volta"]
    assert _resumo(client) == [("tarefa", "Excluída antes", "Casa")]


# RN-90, RN-91: o que a lixeira mostra


def test_rn91_lixeira_lista_projeto_sozinho_e_itens_de_projeto_ativo(
    client: TestClient, relogio: ClockFixo
) -> None:
    lixo = criar_projeto(client, nome="Lixo")["id"]
    criar_tarefa(client, lixo, titulo="Some junto")
    ativo = criar_projeto(client, nome="Casa")["id"]
    tarefa = criar_tarefa(client, ativo, titulo="Pintar")
    lembrete = criar_lembrete(client, ativo, titulo="IPTU")
    documento = _documento(client, ativo, "Planta.pdf")
    anotacao = _anotacao(client, ativo, texto="Medidas da sala\nsegunda linha")
    longa = _anotacao(client, ativo, texto="x" * 80)
    criar_tarefa(client, ativo, titulo="Fica")

    client.delete(f"/api/projetos/{lixo}")
    urls = [
        f"/api/tarefas/{tarefa['id']}",
        f"/api/lembretes/{lembrete['id']}",
        f"/api/documentos/{documento['id']}",
        f"/api/anotacoes/{anotacao['id']}",
        f"/api/anotacoes/{longa['id']}",
    ]
    for dia, url in enumerate(urls, start=15):
        relogio.definir(date(2026, 10, dia))
        assert client.delete(url).status_code == 204

    assert _resumo(client) == [
        ("anotacao", "x" * 59 + "…", "Casa"),
        ("anotacao", "Medidas da sala", "Casa"),
        ("documento", "Planta.pdf", "Casa"),
        ("lembrete", "IPTU", "Casa"),
        ("tarefa", "Pintar", "Casa"),
        ("projeto", "Lixo", None),
    ]
    assert _lixeira(client)[-1] == {
        "tipo": "projeto",
        "id": lixo,
        "titulo": "Lixo",
        "projeto_nome": None,
        "excluido_em": "2026-10-14T15:00:00Z",
        "expira_em": "2026-11-13T15:00:00Z",
        # Hoje é 19/10 (último relógio): 13/11 está a 25 dias.
        "dias_para_expirar": 25,
    }


def test_dias_para_expirar_nao_fica_negativo(client: TestClient, relogio: ClockFixo) -> None:
    projeto_id = criar_projeto(client)["id"]
    client.delete(f"/api/projetos/{projeto_id}")
    relogio.definir(date(2026, 11, 20))

    assert _lixeira(client)[0]["dias_para_expirar"] == 0


def test_rn90_excluidos_nao_contam_em_progresso_nem_avisos(client: TestClient) -> None:
    projeto_id = criar_projeto(client, nome="Casa", acompanhar_progresso=True)["id"]
    criar_tarefa(client, projeto_id, titulo="Fica")
    excluida = criar_tarefa(client, projeto_id, titulo="Some", prazo="2026-10-10")
    lembrete = criar_lembrete(client, projeto_id, vencimento="2026-10-11")
    client.delete(f"/api/tarefas/{excluida['id']}")
    client.delete(f"/api/lembretes/{lembrete['id']}")

    projeto = client.get(f"/api/projetos/{projeto_id}").json()
    assert projeto["progresso"] == {"concluidas": 0, "total": 1}
    assert projeto["avisos"] == 0
    assert client.get("/api/avisos").json() == {"total": 0, "itens": []}
    assert client.get("/api/tarefas/hoje").json() == {"atrasadas": [], "hoje": []}


# RN-93: excluir agora e esvaziar


def test_rn93_excluir_agora_projeto_apaga_dependentes_e_arquivos(
    client: TestClient, settings: Settings
) -> None:
    lixo = _projeto_completo(client, "Lixo")
    ativo = _projeto_completo(client, "Casa")
    client.delete(f"/api/projetos/{lixo}")
    assert len(_arquivos(settings)) == 2

    resposta = client.delete(f"/api/lixeira/projeto/{lixo}")

    assert resposta.status_code == 204
    # Só o projeto ativo sobra, com tudo dele.
    assert _linhas(settings) == dict.fromkeys(TABELAS, 1)
    (arquivo,) = _arquivos(settings)
    assert arquivo.parent.name == ativo
    assert _lixeira(client) == []


def test_rn93_excluir_agora_documento_apaga_o_arquivo(
    client: TestClient, settings: Settings
) -> None:
    projeto_id = criar_projeto(client)["id"]
    some = _documento(client, projeto_id, "some.pdf")
    _documento(client, projeto_id, "fica.pdf")
    client.delete(f"/api/documentos/{some['id']}")

    assert client.delete(f"/api/lixeira/documento/{some['id']}").status_code == 204

    restantes = client.get(f"/api/projetos/{projeto_id}/documentos").json()
    assert [d["nome"] for d in restantes] == ["fica.pdf"]
    assert len(_arquivos(settings)) == 1
    assert _linhas(settings)["documentos"] == 1


@pytest.mark.parametrize("tipo", ["projeto", "tarefa", "lembrete", "documento", "anotacao"])
def test_excluir_agora_o_que_nao_esta_na_lixeira_da_404(client: TestClient, tipo: str) -> None:
    resposta = client.delete(f"/api/lixeira/{tipo}/{uuid.uuid4()}")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["mensagem"] == "Item não encontrado na lixeira."


def test_rn93_esvaziar_apaga_tudo_da_lixeira_e_mais_nada(
    client: TestClient, settings: Settings
) -> None:
    lixo = _projeto_completo(client, "Lixo")
    ativo = criar_projeto(client, nome="Casa")["id"]
    excluido = _documento(client, ativo, "excluido.pdf")
    _documento(client, ativo, "fica.pdf")
    tarefa = criar_tarefa(client, ativo, titulo="Excluída")
    criar_tarefa(client, ativo, titulo="Fica")
    client.delete(f"/api/projetos/{lixo}")
    client.delete(f"/api/documentos/{excluido['id']}")
    client.delete(f"/api/tarefas/{tarefa['id']}")

    assert client.delete("/api/lixeira").status_code == 204

    assert _lixeira(client) == []
    linhas = _linhas(settings)
    assert (linhas["projetos"], linhas["tarefas"], linhas["documentos"]) == (1, 1, 1)
    assert linhas["lembretes"] == linhas["anotacoes"] == 0
    (arquivo,) = _arquivos(settings)
    assert arquivo.parent.name == ativo


class StorageQueFalha(LocalStorage):
    def apagar(self, chave: str) -> None:
        raise OSError("disco ocupado")


def test_rn93_falha_ao_apagar_arquivo_vai_para_o_log_e_nao_desfaz(
    client: TestClient, app: FastAPI, settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    projeto_id = criar_projeto(client)["id"]
    documento = _documento(client, projeto_id)
    client.delete(f"/api/documentos/{documento['id']}")
    app.dependency_overrides[get_storage] = lambda: StorageQueFalha(settings.pasta_anexos)

    with caplog.at_level(logging.ERROR, logger="app.services.lixeira"):
        resposta = client.delete(f"/api/lixeira/documento/{documento['id']}")

    assert resposta.status_code == 204
    assert _linhas(settings)["documentos"] == 0
    assert "Não foi possível apagar o arquivo de documento" in caplog.text


# RN-94: purga na inicialização


@pytest.mark.parametrize(("dias_depois", "purga"), [(31, True), (29, False)])
def test_rn94_inicializacao_purga_o_que_passou_do_prazo(
    client: TestClient, settings: Settings, dias_depois: int, purga: bool
) -> None:
    lixo = _projeto_completo(client, "Lixo")
    ativo = criar_projeto(client, nome="Casa")["id"]
    documento = _documento(client, ativo)
    client.delete(f"/api/projetos/{lixo}")
    client.delete(f"/api/documentos/{documento['id']}")
    # Excluídos em 14/10 (relógio dos testes); o app sobe de novo N dias depois.
    settings.hoje_simulado = date(2026, 10, 14) + timedelta(days=dias_depois)

    with TestClient(create_app(settings)):
        pass

    linhas = _linhas(settings)
    if purga:
        assert linhas == {**dict.fromkeys(TABELAS, 0), "projetos": 1}
        assert _arquivos(settings) == []
    else:
        assert (linhas["projetos"], linhas["documentos"]) == (2, 2)
        assert len(_arquivos(settings)) == 2
