from collections.abc import Iterator

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator

from app.erros import ArquivoGrande, Conflito, NaoEncontrado, Validacao


class Entrada(BaseModel):
    nome: str = Field(min_length=1, max_length=10)
    quantidade: int

    @field_validator("nome")
    @classmethod
    def _nome_preenchido(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("Informe o nome do projeto.")
        return valor


rotas_teste = APIRouter(prefix="/api/_teste")


@rotas_teste.post("/entrada")
def _entrada(dados: Entrada) -> Entrada:
    return dados


@rotas_teste.get("/nao-encontrado")
def _nao_encontrado() -> None:
    raise NaoEncontrado("Projeto não encontrado.")


@rotas_teste.get("/conflito")
def _conflito() -> None:
    raise Conflito()


@rotas_teste.get("/arquivo-grande")
def _arquivo_grande() -> None:
    raise ArquivoGrande()


@rotas_teste.get("/validacao")
def _validacao() -> None:
    raise Validacao(campos={"prazo": "O prazo não pode ser anterior ao início."})


@rotas_teste.get("/falha")
def _falha() -> None:
    raise RuntimeError("detalhe interno que não pode vazar")


@pytest.fixture
def cliente(app: FastAPI) -> Iterator[TestClient]:
    app.include_router(rotas_teste)
    with TestClient(app, raise_server_exceptions=False) as cliente:
        yield cliente


def test_404_rota_inexistente_no_formato_padrao(client: TestClient) -> None:
    resposta = client.get("/api/inexistente")

    assert resposta.status_code == 404
    assert resposta.json() == {
        "erro": {"codigo": "nao_encontrado", "mensagem": "Recurso não encontrado."}
    }


@pytest.mark.parametrize(
    ("rota", "status_http", "codigo", "mensagem"),
    [
        ("nao-encontrado", 404, "nao_encontrado", "Projeto não encontrado."),
        ("conflito", 409, "conflito", "Ação não permitida no estado atual."),
        ("arquivo-grande", 413, "arquivo_grande", "O arquivo passa do limite permitido."),
    ],
)
def test_erros_de_negocio_no_formato_padrao(
    cliente: TestClient, rota: str, status_http: int, codigo: str, mensagem: str
) -> None:
    resposta = cliente.get(f"/api/_teste/{rota}")

    assert resposta.status_code == status_http
    assert resposta.json() == {"erro": {"codigo": codigo, "mensagem": mensagem}}


def test_422_validacao_do_service_com_campos(cliente: TestClient) -> None:
    resposta = cliente.get("/api/_teste/validacao")

    assert resposta.status_code == 422
    assert resposta.json() == {
        "erro": {
            "codigo": "validacao",
            "mensagem": "Revise os campos destacados.",
            "campos": {"prazo": "O prazo não pode ser anterior ao início."},
        }
    }


@pytest.mark.parametrize(
    ("corpo", "campos"),
    [
        ({}, {"nome": "Campo obrigatório.", "quantidade": "Campo obrigatório."}),
        (
            {"nome": "", "quantidade": "abc"},
            {"nome": "Preencha este campo.", "quantidade": "Informe um número inteiro."},
        ),
        (
            {"nome": "x" * 11, "quantidade": 1},
            {"nome": "Use no máximo 10 caracteres."},
        ),
        ({"nome": "   ", "quantidade": 1}, {"nome": "Informe o nome do projeto."}),
    ],
)
def test_422_validacao_da_entrada_no_formato_padrao(
    cliente: TestClient, corpo: dict[str, object], campos: dict[str, str]
) -> None:
    resposta = cliente.post("/api/_teste/entrada", json=corpo)

    assert resposta.status_code == 422
    assert resposta.json() == {
        "erro": {
            "codigo": "validacao",
            "mensagem": "Revise os campos destacados.",
            "campos": campos,
        }
    }


def test_422_json_invalido(cliente: TestClient) -> None:
    resposta = cliente.post(
        "/api/_teste/entrada", content=b"{nome", headers={"content-type": "application/json"}
    )

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["campos"] == {"corpo": "JSON inválido."}


def test_405_metodo_nao_permitido_vira_requisicao_invalida(client: TestClient) -> None:
    resposta = client.delete("/api/saude")

    assert resposta.status_code == 405
    assert resposta.json() == {
        "erro": {"codigo": "requisicao_invalida", "mensagem": "Requisição inválida."}
    }
    assert resposta.headers["allow"] == "GET"


def test_500_erro_interno_sem_detalhes(cliente: TestClient) -> None:
    resposta = cliente.get("/api/_teste/falha")

    assert resposta.status_code == 500
    assert resposta.json() == {
        "erro": {
            "codigo": "erro_interno",
            "mensagem": "Ocorreu um erro inesperado. Tente novamente.",
        }
    }
