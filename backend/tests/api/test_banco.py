from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.sessao import get_session


def test_pragmas_ativos_na_sessao_da_requisicao(app: FastAPI) -> None:
    @app.get("/api/_teste/pragmas")
    def _pragmas(sessao: Annotated[Session, Depends(get_session)]) -> dict[str, object]:
        nomes = ("foreign_keys", "journal_mode", "busy_timeout", "synchronous")
        return {nome: sessao.execute(text(f"PRAGMA {nome}")).scalar_one() for nome in nomes}

    with TestClient(app) as cliente:
        pragmas = cliente.get("/api/_teste/pragmas").json()

    # synchronous NORMAL = 1
    assert pragmas == {
        "foreign_keys": 1,
        "journal_mode": "wal",
        "busy_timeout": 5000,
        "synchronous": 1,
    }
