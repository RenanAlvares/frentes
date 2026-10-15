"""Funções puras de texto."""

import unicodedata


def normalizar_busca(*partes: str) -> str:
    """RN-121: minúsculas, sem acentos e com espaços simples, juntando as partes."""
    texto = " ".join(partes).casefold()
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caractere)
    )
    return " ".join(sem_acentos.split())
