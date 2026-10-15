import pytest

from app.domain.textos import normalizar_busca


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
