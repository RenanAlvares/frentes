import pytest

from app.domain.textos import normalizar_busca, titulo_da_anotacao


@pytest.mark.parametrize(
    ("partes", "esperado"),
    [
        (("Reforma da Cozinha",), "reforma da cozinha"),
        (("Orçamento", "Ação  Pública"), "orcamento acao publica"),
        (("  Ünïcódê\t\nTÉXTO  ",), "unicode texto"),
        (("Nome", ""), "nome"),
        (("",), ""),
    ],
)
def test_rn121_normalizar_busca(partes: tuple[str, ...], esperado: str) -> None:
    assert normalizar_busca(*partes) == esperado


@pytest.mark.parametrize(
    ("titulo", "texto", "esperado"),
    [
        ("Senhas", "Wi-Fi", "Senhas"),
        ("", "Medidas da sala\nsegunda linha", "Medidas da sala"),
        ("", "x" * 60, "x" * 60),
        ("", "x" * 61, "x" * 59 + "…"),
        ("", "", ""),
    ],
)
def test_rn80_titulo_da_anotacao(titulo: str, texto: str, esperado: str) -> None:
    assert titulo_da_anotacao(titulo, texto) == esperado
