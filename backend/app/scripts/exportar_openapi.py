"""Exporta o OpenAPI do app para o front gerar os tipos (05-frontend §3).

Uso (a partir da raiz): uv run --directory backend python -m app.scripts.exportar_openapi \
    ../frontend/openapi.json
"""

import json
import sys
from pathlib import Path

from app.main import create_app


def gerar_openapi() -> str:
    """JSON determinístico: não depende de banco nem de data (o app não é iniciado)."""
    return json.dumps(create_app().openapi(), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    argumentos = sys.argv[1:] if argv is None else argv
    if len(argumentos) != 1:
        sys.stderr.write("Uso: python -m app.scripts.exportar_openapi <destino.json>\n")
        return 2
    # newline="\n": o mesmo arquivo no Windows e no CI (Linux).
    Path(argumentos[0]).write_text(gerar_openapi(), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
