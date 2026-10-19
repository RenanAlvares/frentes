"""Regras puras de documentos (RN-70..72; 06 §8)."""

import pytest

from app.domain.documentos import (
    MIME_PADRAO,
    abre_no_navegador,
    extensao_segura,
    mime_da_extensao,
    nome_renomeado,
)


@pytest.mark.parametrize(
    ("nome", "esperada"),
    [
        ("Contrato.PDF", ".pdf"),
        ("arquivo.tar.gz", ".gz"),
        ("foto.jpeg", ".jpeg"),
        ("con.txt", ".txt"),
        ("../../etc/passwd", ""),
        ("..\\..\\windows\\evil.exe", ".exe"),
        ("sem_extensao", ""),
        (".bashrc", ""),
        ("planilha.a b", ""),
        ("acentuado.ção", ""),
        ("longa." + "a" * 19, "." + "a" * 19),
        ("longa." + "a" * 20, ""),
    ],
)
def test_06_extensao_segura(nome: str, esperada: str) -> None:
    assert extensao_segura(nome) == esperada


@pytest.mark.parametrize(
    ("extensao", "mime"),
    [
        (".pdf", "application/pdf"),
        (".png", "image/png"),
        (".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        (".txt", "text/plain"),
        ("", MIME_PADRAO),
        (".naoexiste", MIME_PADRAO),
    ],
)
def test_mime_pela_extensao(extensao: str, mime: str) -> None:
    assert mime_da_extensao(extensao) == mime


@pytest.mark.parametrize(
    ("extensao", "abre"),
    [
        *((e, True) for e in (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt")),
        *((e, False) for e in (".html", ".htm", ".svg", ".xlsx", ".exe", "")),
    ],
)
def test_rn71_abre_no_navegador(extensao: str, abre: bool) -> None:
    assert abre_no_navegador(extensao) is abre


@pytest.mark.parametrize(
    ("novo", "extensao", "esperado"),
    [
        ("Novo", ".pdf", "Novo.pdf"),
        ("Novo.pdf", ".pdf", "Novo.pdf"),
        ("Novo.PDF", ".pdf", "Novo.PDF"),
        ("Novo.docx", ".pdf", "Novo.docx.pdf"),
        ("Sem extensão", "", "Sem extensão"),
    ],
)
def test_rn72_renomear_mantem_a_extensao(novo: str, extensao: str, esperado: str) -> None:
    assert nome_renomeado(novo, extensao) == esperado
