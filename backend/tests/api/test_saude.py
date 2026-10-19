from datetime import date

from fastapi.testclient import TestClient

from app import __version__
from app.clock import ClockFixo
from app.config import Settings
from app.main import create_app


def test_saude_usa_relogio_fixo(client: TestClient) -> None:
    resposta = client.get("/api/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "ok",
        "versao": __version__,
        "hoje": "2026-10-14",
        "hoje_simulado": False,
        "lixeira_dias": 30,
    }


def test_saude_acompanha_relogio_redefinido(client: TestClient, relogio: ClockFixo) -> None:
    relogio.definir(date(2026, 10, 31))

    assert client.get("/api/saude").json()["hoje"] == "2026-10-31"


def test_rn01_saude_com_hoje_simulado(settings: Settings) -> None:
    settings.hoje_simulado = date(2026, 12, 31)

    with TestClient(create_app(settings)) as cliente:
        corpo = cliente.get("/api/saude").json()

    assert corpo["hoje"] == "2026-12-31"
    assert corpo["hoje_simulado"] is True
