# PyInstaller em modo onedir (06 §11). Do repositório, depois do build do front:
#   npm --prefix frontend run build
#   uv run --directory backend pyinstaller frentes.spec --noconfirm
# Resultado: backend/dist/Frentes/Frentes.exe (com a pasta _internal ao lado).
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

RAIZ = Path(SPECPATH)  # noqa: F821 (definido pelo PyInstaller)

if not (RAIZ / "app" / "static" / "index.html").is_file():
    raise SystemExit("Falta o build do front-end. Rode antes: npm --prefix frontend run build")


def arquivos(pasta: Path, destino: str) -> list[tuple[str, str]]:
    """Os arquivos da pasta (sem __pycache__), nos mesmos caminhos relativos dentro do pacote."""
    return [
        (str(arquivo), str(Path(destino) / arquivo.parent.relative_to(pasta)))
        for arquivo in pasta.rglob("*")
        if arquivo.is_file() and "__pycache__" not in arquivo.parts
    ]


# Os caminhos ficam como no repositório: o código os acha a partir do próprio __file__
# (app/static, alembic.ini e migrations/ dentro de _internal).
dados = [
    *arquivos(RAIZ / "app" / "static", "app/static"),
    *arquivos(RAIZ / "migrations", "migrations"),
    (str(RAIZ / "alembic.ini"), "."),
    # zoneinfo no Windows depende do pacote tzdata (ADR-004).
    *collect_data_files("tzdata"),
]

ocultos = [
    # O uvicorn escolhe loop, protocolo e lifespan pelo nome do módulo.
    *collect_submodules("uvicorn"),
    # migrations/env.py e as versões são carregados do disco: o que só eles importam vem aqui.
    *collect_submodules("alembic"),
    "logging.config",
    "sqlalchemy.dialects.sqlite",
]

a = Analysis(  # noqa: F821
    [str(RAIZ / "empacotamento" / "frentes.py")],
    pathex=[str(RAIZ)],
    datas=dados,
    hiddenimports=ocultos,
    excludes=["pytest", "mypy", "ruff", "PyInstaller"],
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Frentes",
    # Janela de console: mostra o endereço e os avisos (ex.: porta ocupada); fechar encerra o app.
    console=True,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Frentes")  # noqa: F821
