"""Recorrência (RN-30..36). Casos de 07 §3.1: em 2026, 12/10 é segunda e 14/10 é quarta."""

from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.recorrencia import (
    Recorrencia,
    avancar,
    descrever,
    ocorrencias_atrasadas,
    proxima_ocorrencia,
)

SEG, TER, QUA, QUI, SEX, SAB, DOM = range(7)


def diaria(intervalo: int = 1) -> Recorrencia:
    return Recorrencia(frequencia="diaria", intervalo=intervalo)


def semanal(dias: list[int], intervalo: int = 1) -> Recorrencia:
    return Recorrencia(frequencia="semanal", intervalo=intervalo, dias_semana=dias)


def mensal(dia: int, intervalo: int = 1) -> Recorrencia:
    return Recorrencia(frequencia="mensal", intervalo=intervalo, dia_mes=dia)


def anual(dia: int, mes: int, intervalo: int = 1) -> Recorrencia:
    return Recorrencia(frequencia="anual", intervalo=intervalo, dia_mes=dia, mes=mes)


def d(texto: str) -> date:
    return date.fromisoformat(texto)


@pytest.mark.parametrize(
    ("regra", "atual", "hoje", "esperado"),
    [
        pytest.param(diaria(), "2026-10-14", "2026-10-14", "2026-10-15", id="01-diaria"),
        pytest.param(
            diaria(7), "2026-10-01", "2026-10-14", "2026-10-15", id="02-diaria-7-atrasada"
        ),
        pytest.param(diaria(7), "2026-10-20", "2026-10-14", "2026-10-27", id="03-diaria-7-futura"),
        pytest.param(semanal([SEG]), "2026-10-12", "2026-10-14", "2026-10-19", id="04-segunda"),
        pytest.param(
            semanal([SEG, QUA]), "2026-10-12", "2026-10-12", "2026-10-14", id="05-seg-qua"
        ),
        pytest.param(
            semanal([SEG], 2), "2026-10-12", "2026-10-12", "2026-10-26", id="06-quinzenal"
        ),
        pytest.param(semanal([SEG]), "2026-10-14", "2026-10-14", "2026-10-19", id="07-rn33-quarta"),
        pytest.param(mensal(31), "2026-01-31", "2026-01-31", "2026-02-28", id="08-dia31-fev"),
        pytest.param(mensal(31), "2026-02-28", "2026-02-28", "2026-03-31", id="09-nao-gruda-28"),
        pytest.param(mensal(30), "2028-01-30", "2028-01-30", "2028-02-29", id="10-bissexto"),
        pytest.param(mensal(10, 3), "2026-10-10", "2026-10-14", "2027-01-10", id="11-trimestral"),
        pytest.param(mensal(5), "2026-10-03", "2026-10-03", "2026-10-05", id="12-rn33-dia3"),
        pytest.param(mensal(5), "2026-08-05", "2026-10-14", "2026-11-05", id="13-pula-perdidas"),
        pytest.param(anual(29, 2), "2028-02-29", "2028-02-29", "2029-02-28", id="14-29fev"),
        pytest.param(anual(29, 2), "2031-02-28", "2031-02-28", "2032-02-29", id="15-volta-29fev"),
        pytest.param(diaria(), "2026-10-10", "2026-10-14", "2026-10-15", id="16-diaria-atrasada"),
        pytest.param(anual(20, 11, 2), "2026-11-20", "2026-11-20", "2028-11-20", id="17-bienal"),
    ],
)
def test_rn31_rn32_rn33_avancar(regra: Recorrencia, atual: str, hoje: str, esperado: str) -> None:
    assert avancar(regra, d(atual), d(hoje)) == d(esperado)


@pytest.mark.parametrize(
    ("regra", "atual", "hoje", "esperado"),
    [
        pytest.param(mensal(5), "2026-08-05", "2026-10-14", 3, id="mensal-3"),
        pytest.param(diaria(), "2026-10-10", "2026-10-14", 5, id="diaria-5"),
        pytest.param(semanal([SEG]), "2026-10-20", "2026-10-14", 0, id="futura-0"),
        pytest.param(anual(1, 1), "2026-10-14", "2026-10-14", 1, id="hoje-1"),
        pytest.param(diaria(), "2026-01-01", "2026-10-14", 99, id="limite-99"),
        # Qui 01/10 atrasada + sex 02, seg 05, sex 09 e seg 12.
        pytest.param(semanal([SEG, SEX]), "2026-10-01", "2026-10-14", 5, id="semanal"),
    ],
)
def test_rn34_ocorrencias_atrasadas(
    regra: Recorrencia, atual: str, hoje: str, esperado: int
) -> None:
    assert ocorrencias_atrasadas(regra, d(atual), d(hoje)) == esperado


def test_rn32_proxima_ocorrencia_e_estritamente_maior() -> None:
    regra = semanal([SEG, QUA, SEX])

    assert proxima_ocorrencia(regra, d("2026-10-12"), d("2026-10-14")) == d("2026-10-16")
    assert proxima_ocorrencia(regra, d("2026-10-12"), d("2026-10-16")) == d("2026-10-19")
    assert proxima_ocorrencia(mensal(31), d("2026-01-31"), d("2026-04-15")) == d("2026-04-30")


@pytest.mark.parametrize(
    ("regra", "texto"),
    [
        (diaria(), "todo dia"),
        (diaria(7), "a cada 7 dias"),
        (semanal([SEG]), "toda segunda"),
        (semanal([SAB]), "todo sábado"),
        (semanal([SEG, QUA, SEX]), "toda semana: segunda, quarta e sexta"),
        (semanal([SEG, TER, QUA, QUI, SEX]), "de segunda a sexta"),
        (semanal(list(range(7))), "todo dia"),
        (semanal([SEG, QUA], 2), "a cada 2 semanas: segunda e quarta"),
        (mensal(5), "todo dia 5"),
        (mensal(10, 3), "a cada 3 meses, no dia 10"),
        (mensal(31), "todo dia 31 (ou o último dia do mês)"),
        (mensal(29), "todo dia 29 (ou o último dia do mês)"),
        (mensal(30), "todo dia 30 (ou o último dia do mês)"),
        (anual(20, 11), "todo ano em 20/11"),
        (anual(20, 11, 2), "a cada 2 anos em 20/11"),
        # Fora da tabela de RN-35, mas pela mesma lógica:
        (semanal([DOM]), "todo domingo"),
        (anual(5, 3), "todo ano em 05/03"),
    ],
)
def test_rn35_descrever(regra: Recorrencia, texto: str) -> None:
    assert descrever(regra) == texto


def _erros(**dados: Any) -> dict[str, str]:
    with pytest.raises(ValidationError) as excecao:
        Recorrencia(**dados)
    return {
        ".".join(str(parte) for parte in erro["loc"]) or "regra": erro["msg"].removeprefix(
            "Value error, "
        )
        for erro in excecao.value.errors()
    }


@pytest.mark.parametrize(
    ("dados", "campo", "mensagem"),
    [
        ({"frequencia": "semanal"}, "dias_semana", "Escolha pelo menos um dia da semana."),
        (
            {"frequencia": "semanal", "dias_semana": []},
            "dias_semana",
            "Escolha pelo menos um dia da semana.",
        ),
        ({"frequencia": "semanal", "dias_semana": [7]}, "dias_semana.0", ""),
        ({"frequencia": "semanal", "dias_semana": [-1]}, "dias_semana.0", ""),
        ({"frequencia": "mensal"}, "dia_mes", "Informe o dia do mês."),
        ({"frequencia": "mensal", "dia_mes": 32}, "dia_mes", ""),
        ({"frequencia": "anual", "dia_mes": 5}, "mes", "Informe o mês."),
        ({"frequencia": "anual", "mes": 5}, "dia_mes", "Informe o dia do mês."),
        ({"frequencia": "diaria", "intervalo": 0}, "intervalo", ""),
        ({"frequencia": "diaria", "intervalo": 366}, "intervalo", ""),
        (
            {"frequencia": "diaria", "dias_semana": [0]},
            "dias_semana",
            "Não se aplica a esta frequência.",
        ),
        (
            {"frequencia": "semanal", "dias_semana": [0], "dia_mes": 3},
            "dia_mes",
            "Não se aplica a esta frequência.",
        ),
        (
            {"frequencia": "mensal", "dia_mes": 3, "mes": 4},
            "mes",
            "Não se aplica a esta frequência.",
        ),
        ({"frequencia": "horaria"}, "frequencia", ""),
        ({"frequencia": "anual", "dia_mes": 31, "mes": 4}, "regra", "Dia inválido para o mês."),
        ({"frequencia": "anual", "dia_mes": 30, "mes": 2}, "regra", "Dia inválido para o mês."),
    ],
)
def test_rn30_validacao(dados: dict[str, Any], campo: str, mensagem: str) -> None:
    erros = _erros(**dados)

    assert campo in erros, erros
    if mensagem:
        assert erros[campo] == mensagem


def test_rn30_regras_validas_e_dias_normalizados() -> None:
    assert semanal([QUA, SEG, QUA]).dias_semana == [SEG, QUA]
    assert anual(29, 2).dia_mes == 29
    assert diaria().model_dump() == {
        "frequencia": "diaria",
        "intervalo": 1,
        "dias_semana": None,
        "dia_mes": None,
        "mes": None,
    }
