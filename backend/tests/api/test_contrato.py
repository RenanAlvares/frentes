"""Contrato da API: OpenAPI exportado para o front (04-api Convenções, 05-frontend §3)."""

import json
import re
from pathlib import Path

import pytest
from fastapi import FastAPI

from app.scripts.exportar_openapi import main


def test_exportacao_e_deterministica_e_igual_ao_openapi_do_app(
    tmp_path: Path, app: FastAPI
) -> None:
    primeiro, segundo = tmp_path / "a.json", tmp_path / "b.json"

    assert main([str(primeiro)]) == 0
    assert main([str(segundo)]) == 0

    conteudo = primeiro.read_bytes()
    assert conteudo == segundo.read_bytes()
    assert conteudo.endswith(b"}\n")
    assert b"\r\n" not in conteudo
    assert json.loads(conteudo) == app.openapi()


def test_exportacao_sem_destino_mostra_uso(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "Uso:" in capsys.readouterr().err


def test_toda_operacao_tem_operation_id_explicito_em_snake_case(app: FastAPI) -> None:
    ids = []
    for caminho, metodos in app.openapi()["paths"].items():
        for metodo, operacao in metodos.items():
            id_ = operacao["operationId"]
            # O id que o FastAPI gera sozinho termina com o método (`obter_saude_api_saude_get`).
            explicito = re.fullmatch(r"[a-z][a-z0-9_]*", id_) and not id_.endswith(f"_{metodo}")
            assert explicito, f"{metodo.upper()} {caminho}: {id_}"
            ids.append(id_)

    assert ids
    assert len(set(ids)) == len(ids)


def test_erros_no_contrato_usam_o_formato_padrao(app: FastAPI) -> None:
    schema = app.openapi()
    referencia = "#/components/schemas/ErroResposta"

    for caminho, metodos in schema["paths"].items():
        for metodo, operacao in metodos.items():
            padrao = operacao["responses"]["default"]["content"]["application/json"]["schema"]
            assert padrao == {"$ref": referencia}, f"{metodo.upper()} {caminho}"
    assert "HTTPValidationError" not in schema["components"]["schemas"]
