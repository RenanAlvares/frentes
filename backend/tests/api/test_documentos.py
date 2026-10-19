"""Documentos: RN-70..73 na API. 07 §3.7; hoje = 2026-10-14."""

import re
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.clock import ClockFixo
from app.config import Settings
from tests.conftest import criar_projeto

MB = 1024 * 1024
PDF = b"%PDF-1.4 conteudo"


@pytest.fixture
def settings(pasta_dados: Path) -> Settings:
    # Limite baixo (1 MB) para testar o 413 sem arquivos enormes.
    return Settings(
        _env_file=None,
        data_dir=pasta_dados,
        database_url="",
        hoje_simulado=None,
        abrir_navegador=False,
        max_upload_mb=1,
    )


@pytest.fixture
def projeto_id(client: TestClient) -> str:
    return str(criar_projeto(client, nome="Casa")["id"])


def _enviar(client: TestClient, projeto_id: str, *arquivos: tuple[str, bytes]) -> Any:
    partes = [("arquivos", (nome, conteudo)) for nome, conteudo in arquivos]
    return client.post(f"/api/projetos/{projeto_id}/documentos", files=partes)


def _criados(client: TestClient, projeto_id: str, *arquivos: tuple[str, bytes]) -> list[Any]:
    resposta = _enviar(client, projeto_id, *arquivos)
    assert resposta.status_code == 201, resposta.text
    criados: list[Any] = resposta.json()
    return criados


def _lista(client: TestClient, projeto_id: str) -> list[Any]:
    resposta = client.get(f"/api/projetos/{projeto_id}/documentos")
    assert resposta.status_code == 200, resposta.text
    lista: list[Any] = resposta.json()
    return lista


def _no_disco(settings: Settings) -> list[Path]:
    raiz = settings.pasta_anexos
    return sorted(p for p in raiz.rglob("*") if p.is_file()) if raiz.exists() else []


# RN-70


def test_rn70_upload_de_dois_arquivos(
    client: TestClient, settings: Settings, projeto_id: str
) -> None:
    pdf, planilha = _criados(
        client, projeto_id, ("Contrato.PDF", PDF), ("Orçamento.xlsx", b"planilha")
    )

    assert pdf == {
        "id": pdf["id"],
        "projeto_id": projeto_id,
        "nome": "Contrato.PDF",
        "extensao": ".pdf",
        "mime": "application/pdf",
        "tamanho_bytes": len(PDF),
        "abre_no_navegador": True,
        "criado_em": "2026-10-14T15:00:00Z",
    }
    assert planilha["extensao"] == ".xlsx"
    assert planilha["abre_no_navegador"] is False
    arquivos = _no_disco(settings)
    assert len(arquivos) == 2
    assert {p.parent.name for p in arquivos} == {projeto_id}
    assert all(re.fullmatch(r"[0-9a-f]{32}\.(pdf|xlsx)", p.name) for p in arquivos)
    assert sorted(p.read_bytes() for p in arquivos) == sorted([PDF, b"planilha"])
    assert {d["nome"] for d in _lista(client, projeto_id)} == {"Contrato.PDF", "Orçamento.xlsx"}


def test_rn70_acima_do_limite_nada_fica_gravado(
    client: TestClient, settings: Settings, projeto_id: str
) -> None:
    resposta = _enviar(client, projeto_id, ("pequeno.txt", b"ok"), ("grande.bin", b"x" * (MB + 1)))

    assert resposta.status_code == 413
    assert resposta.json()["erro"] == {
        "codigo": "arquivo_grande",
        "mensagem": "“grande.bin” passa do limite de 1 MB.",
    }
    assert _lista(client, projeto_id) == []
    assert _no_disco(settings) == []


def test_rn70_exatamente_no_limite_e_aceito(client: TestClient, projeto_id: str) -> None:
    (documento,) = _criados(client, projeto_id, ("limite.bin", b"x" * MB))

    assert documento["tamanho_bytes"] == MB


@pytest.mark.parametrize(
    ("nome", "extensao"), [("../../etc/passwd", ""), ("con.txt", ".txt"), ("a\\..\\b.exe", ".exe")]
)
def test_rn70_nome_do_usuario_nunca_vira_caminho(
    client: TestClient, settings: Settings, projeto_id: str, nome: str, extensao: str
) -> None:
    (documento,) = _criados(client, projeto_id, (nome, b"conteudo"))

    assert documento["nome"] == nome
    assert documento["extensao"] == extensao
    (arquivo,) = _no_disco(settings)
    assert arquivo.parent == settings.pasta_anexos / projeto_id
    assert re.fullmatch(rf"[0-9a-f]{{32}}{re.escape(extensao)}", arquivo.name)


def test_upload_sem_arquivos_da_422(client: TestClient, projeto_id: str) -> None:
    resposta = client.post(f"/api/projetos/{projeto_id}/documentos")

    assert resposta.status_code == 422


def test_upload_em_projeto_inexistente_da_404(client: TestClient, settings: Settings) -> None:
    resposta = _enviar(client, str(uuid.uuid4()), ("a.pdf", PDF))

    assert resposta.status_code == 404
    assert _no_disco(settings) == []


# RN-71


@pytest.mark.parametrize(
    ("nome", "disposicao", "mime"),
    [
        ("Relatório final.pdf", "inline", "application/pdf"),
        ("foto.png", "inline", "image/png"),
        ("notas.txt", "inline", "text/plain"),
        ("pagina.html", "attachment", "text/html"),
        ("desenho.svg", "attachment", "image/svg+xml"),
        ("planilha.xlsx", "attachment", None),
    ],
)
def test_rn71_download(
    client: TestClient, projeto_id: str, nome: str, disposicao: str, mime: str | None
) -> None:
    (documento,) = _criados(client, projeto_id, (nome, b"conteudo do arquivo"))

    resposta = client.get(f"/api/documentos/{documento['id']}/arquivo")

    assert resposta.status_code == 200
    assert resposta.content == b"conteudo do arquivo"
    assert resposta.headers["x-content-type-options"] == "nosniff"
    tipo, parametro = resposta.headers["content-disposition"].split("; ")
    assert tipo == disposicao
    assert parametro.startswith("filename*=UTF-8''")
    if mime:
        assert resposta.headers["content-type"].startswith(mime)


def test_rn71_nome_com_acento_no_filename(client: TestClient, projeto_id: str) -> None:
    (documento,) = _criados(client, projeto_id, ("Relatório final.pdf", PDF))

    resposta = client.get(f"/api/documentos/{documento['id']}/arquivo")

    assert resposta.headers["content-disposition"] == (
        "inline; filename*=UTF-8''Relat%C3%B3rio%20final.pdf"
    )


def test_download_sem_o_arquivo_no_disco_da_404(
    client: TestClient, settings: Settings, projeto_id: str
) -> None:
    (documento,) = _criados(client, projeto_id, ("a.pdf", PDF))
    for arquivo in _no_disco(settings):
        arquivo.unlink()

    resposta = client.get(f"/api/documentos/{documento['id']}/arquivo")

    assert resposta.status_code == 404


# RN-72


@pytest.mark.parametrize(
    ("novo", "esperado"),
    [("Novo", "Novo.pdf"), ("  Novo.PDF  ", "Novo.PDF"), ("Novo.docx", "Novo.docx.pdf")],
)
def test_rn72_renomear_mantem_a_extensao(
    client: TestClient, relogio: ClockFixo, projeto_id: str, novo: str, esperado: str
) -> None:
    (documento,) = _criados(client, projeto_id, ("Contrato.pdf", PDF))
    relogio.definir(date(2026, 10, 15))

    resposta = client.patch(f"/api/documentos/{documento['id']}", json={"nome": novo})

    assert resposta.status_code == 200, resposta.text
    assert resposta.json() == {**documento, "nome": esperado}
    baixado = client.get(f"/api/documentos/{documento['id']}/arquivo")
    assert baixado.headers["content-disposition"].endswith(esperado)


@pytest.mark.parametrize(
    ("nome", "mensagem"),
    [
        ("pasta/arquivo", "O nome não pode ter / nem \\."),
        ("pasta\\arquivo", "O nome não pode ter / nem \\."),
        ("   ", "Informe o nome do documento."),
        ("a" * 256, "Use no máximo 255 caracteres."),
        ("a" * 252, "Use no máximo 255 caracteres, contando a extensão."),
    ],
)
def test_rn72_nome_invalido_da_422(
    client: TestClient, projeto_id: str, nome: str, mensagem: str
) -> None:
    (documento,) = _criados(client, projeto_id, ("Contrato.pdf", PDF))

    resposta = client.patch(f"/api/documentos/{documento['id']}", json={"nome": nome})

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["campos"] == {"nome": mensagem}


# RN-73, RN-90, RN-91


def test_rn73_lista_mais_recentes_primeiro(
    client: TestClient, relogio: ClockFixo, projeto_id: str
) -> None:
    _criados(client, projeto_id, ("antigo.pdf", PDF))
    relogio.definir(date(2026, 10, 15))
    _criados(client, projeto_id, ("b.pdf", PDF), ("a.pdf", PDF))

    assert [d["nome"] for d in _lista(client, projeto_id)] == ["a.pdf", "b.pdf", "antigo.pdf"]


def test_rn90_excluir_manda_para_a_lixeira_e_restaurar_volta(
    client: TestClient, settings: Settings, projeto_id: str
) -> None:
    (documento,) = _criados(client, projeto_id, ("a.pdf", PDF))
    url = f"/api/documentos/{documento['id']}"

    assert client.delete(url).status_code == 204

    assert _lista(client, projeto_id) == []
    assert client.get(f"{url}/arquivo").status_code == 404
    assert client.patch(url, json={"nome": "b"}).status_code == 404
    # O arquivo só sai do disco na purga da lixeira (RN-93).
    assert len(_no_disco(settings)) == 1

    restaurar = client.post(f"/api/lixeira/documento/{documento['id']}/restaurar")
    assert restaurar.status_code == 204
    assert _lista(client, projeto_id) == [documento]


def test_rn91_documentos_de_projeto_excluido_somem(client: TestClient, projeto_id: str) -> None:
    (documento,) = _criados(client, projeto_id, ("a.pdf", PDF))
    client.delete(f"/api/projetos/{projeto_id}")

    assert client.get(f"/api/projetos/{projeto_id}/documentos").status_code == 404
    assert client.get(f"/api/documentos/{documento['id']}/arquivo").status_code == 404
