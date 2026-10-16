"""Recorrência de tarefas repetidas e lembretes (RN-30..36). Puro: sem banco e sem relógio."""

import calendar
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from app.domain.enums import Frequencia

LIMITE_ATRASADAS = 99  # RN-34

DIAS = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")  # 0 = segunda
_FEMININOS = {0, 1, 2, 3, 4}  # "toda segunda", mas "todo sábado"

DiaSemana = Annotated[int, Field(ge=0, le=6)]


class Recorrencia(BaseModel):
    """RN-30. Campos que não se aplicam à frequência ficam `null`."""

    model_config = ConfigDict(frozen=True)

    frequencia: Frequencia
    intervalo: int = Field(default=1, ge=1, le=365)
    dias_semana: list[DiaSemana] | None = Field(default=None, validate_default=True)
    dia_mes: int | None = Field(default=None, ge=1, le=31, validate_default=True)
    mes: int | None = Field(default=None, ge=1, le=12, validate_default=True)

    @field_validator("dias_semana")
    @classmethod
    def _dias(cls, valor: list[int] | None, info: ValidationInfo) -> list[int] | None:
        semanal = info.data.get("frequencia") == Frequencia.SEMANAL
        if semanal and not valor:
            raise ValueError("Escolha pelo menos um dia da semana.")
        if not semanal and valor is not None:
            raise ValueError("Não se aplica a esta frequência.")
        # Formato de RN-30: sem repetição e ordenado.
        return sorted(set(valor)) if valor else valor

    @field_validator("dia_mes")
    @classmethod
    def _dia_mes(cls, valor: int | None, info: ValidationInfo) -> int | None:
        usa = info.data.get("frequencia") in (Frequencia.MENSAL, Frequencia.ANUAL)
        if usa and valor is None:
            raise ValueError("Informe o dia do mês.")
        if not usa and valor is not None:
            raise ValueError("Não se aplica a esta frequência.")
        return valor

    @field_validator("mes")
    @classmethod
    def _mes(cls, valor: int | None, info: ValidationInfo) -> int | None:
        anual = info.data.get("frequencia") == Frequencia.ANUAL
        if anual and valor is None:
            raise ValueError("Informe o mês.")
        if not anual and valor is not None:
            raise ValueError("Não se aplica a esta frequência.")
        return valor

    @model_validator(mode="after")
    def _dia_existe_no_mes(self) -> "Recorrencia":
        # Anual: o dia tem de existir no mês (29/02 vale; vira 28/02 nos anos não bissextos).
        # 2000 é bissexto, então fevereiro aceita 29.
        dia, mes = self.dia_mes, self.mes
        if dia is not None and mes is not None and dia > calendar.monthrange(2000, mes)[1]:
            raise ValueError("Dia inválido para o mês.")
        return self


def _no_mes(ano: int, mes: int, dia: int) -> date:
    """O dia pedido ou, se o mês não tem esse dia, o último dia do mês (RN-31)."""
    return date(ano, mes, min(dia, calendar.monthrange(ano, mes)[1]))


def _somar_meses(base: date, meses: int) -> tuple[int, int]:
    total = base.year * 12 + (base.month - 1) + meses
    return total // 12, total % 12 + 1


def _sequencia(regra: Recorrencia, ancora: date, depois_de: date) -> Iterator[date]:
    """Datas de RN-31 em ordem crescente, a partir do primeiro bloco que pode passar `depois_de`."""
    n = regra.intervalo
    if regra.frequencia == Frequencia.DIARIA:
        k = max(0, (depois_de - ancora).days // n)
        while True:
            yield ancora + timedelta(days=k * n)
            k += 1
    elif regra.frequencia == Frequencia.SEMANAL:
        inicio_semana = ancora - timedelta(days=ancora.weekday())
        k = max(0, (depois_de - inicio_semana).days // (7 * n))
        dias = regra.dias_semana or []
        while True:
            semana = inicio_semana + timedelta(weeks=k * n)
            for dia in dias:
                yield semana + timedelta(days=dia)
            k += 1
    elif regra.frequencia == Frequencia.MENSAL:
        meses = (depois_de.year - ancora.year) * 12 + depois_de.month - ancora.month
        k = max(0, meses // n)
        while True:
            ano, mes = _somar_meses(ancora, k * n)
            yield _no_mes(ano, mes, regra.dia_mes or 1)
            k += 1
    else:
        k = max(0, (depois_de.year - ancora.year) // n)
        while True:
            yield _no_mes(ancora.year + k * n, regra.mes or 1, regra.dia_mes or 1)
            k += 1


def proxima_ocorrencia(regra: Recorrencia, ancora: date, depois_de: date) -> date:
    """RN-32: primeira data da sequência ancorada em `ancora` estritamente maior que `depois_de`."""
    return next(data for data in _sequencia(regra, ancora, depois_de) if data > depois_de)


def avancar(regra: Recorrencia, atual: date, hoje: date) -> date:
    """RN-32: pula as ocorrências perdidas e vai para a primeira data futura (ou a seguinte)."""
    return proxima_ocorrencia(regra, atual, max(atual, hoje))


def ocorrencias_atrasadas(regra: Recorrencia, atual: date, hoje: date) -> int:
    """RN-34: 0 se ainda não venceu; senão 1 + ocorrências em (atual, hoje], até 99."""
    if atual > hoje:
        return 0
    total = 1
    for data in _sequencia(regra, atual, atual):
        if data <= atual:
            continue
        if data > hoje or total == LIMITE_ATRASADAS:
            break
        total += 1
    return total


def _lista(itens: list[str]) -> str:
    return itens[0] if len(itens) == 1 else f"{', '.join(itens[:-1])} e {itens[-1]}"


def descrever(regra: Recorrencia) -> str:
    """RN-35: texto da regra em português (vai para a API como `recorrencia_descricao`)."""
    n = regra.intervalo
    if regra.frequencia == Frequencia.DIARIA:
        return "todo dia" if n == 1 else f"a cada {n} dias"
    if regra.frequencia == Frequencia.SEMANAL:
        dias = regra.dias_semana or []
        nomes = _lista([DIAS[dia] for dia in dias])
        if n > 1:
            return f"a cada {n} semanas: {nomes}"
        if dias == list(range(7)):
            return "todo dia"
        if dias == list(range(5)):
            return "de segunda a sexta"
        if len(dias) == 1:
            return f"{'toda' if dias[0] in _FEMININOS else 'todo'} {nomes}"
        return f"toda semana: {nomes}"
    if regra.frequencia == Frequencia.MENSAL:
        dia = regra.dia_mes or 1
        fim = " (ou o último dia do mês)" if dia >= 29 else ""
        return f"todo dia {dia}{fim}" if n == 1 else f"a cada {n} meses, no dia {dia}{fim}"
    data = f"{regra.dia_mes or 1:02d}/{regra.mes or 1:02d}"
    return f"todo ano em {data}" if n == 1 else f"a cada {n} anos em {data}"
