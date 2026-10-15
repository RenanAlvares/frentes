"""Front-end servido pelo back-end (06 §10; 04-api, SPA)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clock import ClockFixo, get_clock
from app.config import Settings
from app.main import create_app

INDEX = "<!doctype html><title>Frentes</title><div id=root></div>"
ERRO_404 = {"erro": {"codigo": "nao_encontrado", "mensagem": "Recurso não encontrado."}}


def _cliente(settings: Settings, relogio: ClockFixo, pasta_static: Path) -> Iterator[TestClient]:
    app = create_app(settings, pasta_static=pasta_static)
    app.dependency_overrides[get_clock] = lambda: relogio
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def com_build(tmp_path: Path, settings: Settings, relogio: ClockFixo) -> Iterator[TestClient]:
    pasta = tmp_path / "static"
    (pasta / "assets").mkdir(parents=True)
    (pasta / "index.html").write_text(INDEX, encoding="utf-8")
    (pasta / "assets" / "index-abc123.js").write_text("console.log(1)", encoding="utf-8")
    yield from _cliente(settings, relogio, pasta)


@pytest.fixture
def sem_build(tmp_path: Path, settings: Settings, relogio: ClockFixo) -> Iterator[TestClient]:
    yield from _cliente(settings, relogio, tmp_path / "static-inexistente")


@pytest.mark.parametrize(
    "url", ["/", "/hoje", "/projetos/abc", "/projetos/abc?tarefa=1", "/configuracoes"]
)
def test_rotas_do_front_devolvem_o_index_sem_cache(com_build: TestClient, url: str) -> None:
    resposta = com_build.get(url)

    assert resposta.status_code == 200
    assert resposta.text == INDEX
    assert resposta.headers["content-type"].startswith("text/html")
    assert resposta.headers["cache-control"] == "no-cache"


def test_assets_com_cache_longo(com_build: TestClient) -> None:
    resposta = com_build.get("/assets/index-abc123.js")

    assert resposta.status_code == 200
    assert resposta.text == "console.log(1)"
    assert resposta.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.parametrize(
    ("metodo", "url"),
    [
        ("GET", "/api/inexistente"),
        ("POST", "/api/inexistente"),
        ("GET", "/api"),
        ("GET", "/assets/nao-existe.js"),
        ("POST", "/projetos"),
    ],
)
def test_404_de_verdade_no_formato_de_erro_nunca_o_index(
    com_build: TestClient, metodo: str, url: str
) -> None:
    resposta = com_build.request(metodo, url)

    assert resposta.status_code == 404
    assert resposta.json() == ERRO_404


def test_metodo_errado_em_rota_da_api_continua_405(com_build: TestClient) -> None:
    resposta = com_build.delete("/api/saude")

    assert resposta.status_code == 405
    assert resposta.json()["erro"]["codigo"] == "requisicao_invalida"


def test_sem_build_mostra_como_rodar_o_front(sem_build: TestClient) -> None:
    resposta = sem_build.get("/hoje")

    assert resposta.status_code == 200
    assert "npm --prefix frontend run dev" in resposta.text
    assert "npm --prefix frontend run build" in resposta.text
    assert sem_build.get("/assets/index-abc123.js").json() == ERRO_404
    assert sem_build.get("/api/saude").status_code == 200
