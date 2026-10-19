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


RESUMO_ANOTACAO = 60


def titulo_da_anotacao(titulo: str, texto: str) -> str:
    """O título, ou (RN-80: título opcional) a primeira linha do texto, cortada em 60 caracteres."""
    if titulo:
        return titulo
    primeira_linha = texto.splitlines()[0] if texto else ""
    if len(primeira_linha) <= RESUMO_ANOTACAO:
        return primeira_linha
    return primeira_linha[: RESUMO_ANOTACAO - 1].rstrip() + "…"
