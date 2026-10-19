"""Ponto de entrada do executável (PyInstaller, 06 §11): o mesmo `frentes` da linha de comando."""

import sys

from app.cli import main

if __name__ == "__main__":
    sys.exit(main())
