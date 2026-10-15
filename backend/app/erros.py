"""Erros de negócio e handlers no formato padrão da API (04 — Formato de erro)."""

import logging
from collections.abc import Mapping, Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.erros import ErroDetalhe, ErroResposta

logger = logging.getLogger(__name__)


class ErroApp(Exception):
    status_http = 500
    codigo = "erro_interno"
    mensagem_padrao = "Ocorreu um erro inesperado. Tente novamente."

    def __init__(self, mensagem: str | None = None) -> None:
        self.mensagem = mensagem or self.mensagem_padrao
        super().__init__(self.mensagem)


class NaoEncontrado(ErroApp):
    status_http = 404
    codigo = "nao_encontrado"
    mensagem_padrao = "Recurso não encontrado."


class Conflito(ErroApp):
    status_http = 409
    codigo = "conflito"
    mensagem_padrao = "Ação não permitida no estado atual."


class ArquivoGrande(ErroApp):
    status_http = 413
    codigo = "arquivo_grande"
    mensagem_padrao = "O arquivo passa do limite permitido."


class Validacao(ErroApp):
    status_http = 422
    codigo = "validacao"
    mensagem_padrao = "Revise os campos destacados."

    def __init__(
        self, mensagem: str | None = None, *, campos: dict[str, str] | None = None
    ) -> None:
        super().__init__(mensagem)
        self.campos = campos or {}


# Erros HTTP fora da tabela de 04 (ex.: 405) mantêm o status com este código.
CODIGO_REQUISICAO_INVALIDA = "requisicao_invalida"

_MENSAGENS_VALIDACAO = {
    "missing": "Campo obrigatório.",
    "string_type": "Informe um texto.",
    "string_too_long": "Use no máximo {max_length} caracteres.",
    "int_type": "Informe um número inteiro.",
    "int_parsing": "Informe um número inteiro.",
    "int_from_float": "Informe um número inteiro.",
    "bool_type": "Informe verdadeiro ou falso.",
    "bool_parsing": "Informe verdadeiro ou falso.",
    "date_type": "Informe uma data válida (AAAA-MM-DD).",
    "date_parsing": "Informe uma data válida (AAAA-MM-DD).",
    "date_from_datetime_parsing": "Informe uma data válida (AAAA-MM-DD).",
    "uuid_type": "Identificador inválido.",
    "uuid_parsing": "Identificador inválido.",
    "enum": "Valor não permitido.",
    "literal_error": "Valor não permitido.",
    "greater_than": "Informe um valor maior que {gt}.",
    "greater_than_equal": "Informe um valor maior ou igual a {ge}.",
    "less_than": "Informe um valor menor que {lt}.",
    "less_than_equal": "Informe um valor menor ou igual a {le}.",
    "json_invalid": "JSON inválido.",
}
_ORIGENS = {"body", "query", "path", "header", "cookie"}


def _mensagem_campo(erro: Mapping[str, object]) -> str:
    tipo = str(erro.get("type", ""))
    ctx = erro.get("ctx")
    contexto = ctx if isinstance(ctx, Mapping) else {}
    if tipo in {"value_error", "assertion_error"}:
        # Mensagem de validador próprio (ex.: "Informe o nome do projeto.").
        return str(contexto.get("error", erro.get("msg", "")))
    if tipo == "string_too_short":
        minimo = contexto.get("min_length", 1)
        return "Preencha este campo." if minimo == 1 else f"Use pelo menos {minimo} caracteres."
    return _MENSAGENS_VALIDACAO.get(tipo, "Valor inválido.").format(**contexto)


def _nome_campo(erro: Mapping[str, object]) -> str:
    if erro.get("type") == "json_invalid":
        return "corpo"
    loc = erro.get("loc")
    partes: Sequence[object] = loc if isinstance(loc, tuple | list) else ()
    if partes and partes[0] in _ORIGENS:
        partes = partes[1:]
    return ".".join(str(parte) for parte in partes) or "corpo"


def _resposta(
    status_http: int,
    codigo: str,
    mensagem: str,
    campos: dict[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    corpo = ErroResposta(erro=ErroDetalhe(codigo=codigo, mensagem=mensagem, campos=campos))
    return JSONResponse(
        corpo.model_dump(exclude_none=True), status_code=status_http, headers=headers
    )


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(ErroApp)
    async def _erro_app(_request: Request, erro: ErroApp) -> JSONResponse:
        campos = erro.campos if isinstance(erro, Validacao) else None
        return _resposta(erro.status_http, erro.codigo, erro.mensagem, campos)

    @app.exception_handler(RequestValidationError)
    async def _erro_validacao(_request: Request, erro: RequestValidationError) -> JSONResponse:
        campos: dict[str, str] = {}
        for item in erro.errors():
            campos.setdefault(_nome_campo(item), _mensagem_campo(item))
        return _resposta(422, Validacao.codigo, Validacao.mensagem_padrao, campos)

    @app.exception_handler(StarletteHTTPException)
    async def _erro_http(_request: Request, erro: StarletteHTTPException) -> JSONResponse:
        if erro.status_code == 404:
            return _resposta(
                404, NaoEncontrado.codigo, NaoEncontrado.mensagem_padrao, headers=erro.headers
            )
        return _resposta(
            erro.status_code,
            CODIGO_REQUISICAO_INVALIDA,
            "Requisição inválida.",
            headers=erro.headers,
        )

    @app.exception_handler(Exception)
    async def _erro_inesperado(request: Request, _erro: Exception) -> JSONResponse:
        logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
        return _resposta(500, ErroApp.codigo, ErroApp.mensagem_padrao)
