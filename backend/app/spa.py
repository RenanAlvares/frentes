"""Front-end servido pelo back-end no modo de uso local (06 §10; 04-api, SPA)."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

PASTA_STATIC = Path(__file__).resolve().parent / "static"
_PREFIXOS_FORA_DA_SPA = ("/api", "/assets")

_SEM_BUILD = """<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<title>Frentes</title>
<style>body { font-family: system-ui, sans-serif; max-width: 40rem; margin: 4rem auto; }</style>
<body>
<h1>Frentes</h1>
<p>O front-end ainda não foi gerado.</p>
<p>Em desenvolvimento, rode <code>npm --prefix frontend run dev</code> e acesse
<a href="http://localhost:5173">http://localhost:5173</a>.</p>
<p>Para usar o app por aqui, gere o build com <code>npm --prefix frontend run build</code>
e reinicie o Frentes.</p>
</body>
</html>
"""


class _AssetsImutaveis(StaticFiles):
    """Arquivos do build levam hash no nome: podem ficar em cache para sempre."""

    def file_response(
        self,
        full_path: str | os.PathLike[str],
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        resposta = super().file_response(full_path, stat_result, scope, status_code)
        resposta.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resposta


def montar_assets(app: FastAPI, pasta_static: Path) -> None:
    """`/assets` só existe com build; sem ele, o 404 sai no formato de erro da API."""
    app.state.pasta_static = pasta_static
    if (pasta_static / "assets").is_dir():
        app.mount("/assets", _AssetsImutaveis(directory=pasta_static / "assets"), name="assets")


def _eh_rota_da_spa(request: Request) -> bool:
    caminho = request.url.path
    fora = any(caminho == p or caminho.startswith(f"{p}/") for p in _PREFIXOS_FORA_DA_SPA)
    return request.method in ("GET", "HEAD") and not fora


def responder_spa(request: Request) -> Response | None:
    """Para um 404: `index.html` se for rota do React Router; `None` se o 404 é de verdade."""
    if not _eh_rota_da_spa(request):
        return None
    pasta_static: Path = request.app.state.pasta_static
    index = pasta_static / "index.html"
    if index.is_file():
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
    return HTMLResponse(_SEM_BUILD, headers={"Cache-Control": "no-cache"})
