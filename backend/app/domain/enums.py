"""Enums do domínio (03-dados, Enums). Os demais entram com as tabelas que os usam."""

from enum import StrEnum


class StatusProjeto(StrEnum):
    PLANEJADO = "planejado"
    EM_ANDAMENTO = "em_andamento"
    AGUARDANDO = "aguardando"
    CONCLUIDO = "concluido"


class CorProjeto(StrEnum):
    AZUL = "azul"
    VERDE = "verde"
    ROXO = "roxo"
    LARANJA = "laranja"
    ROSA = "rosa"
    VERMELHO = "vermelho"
    CIANO = "ciano"
    CINZA = "cinza"


class StatusTarefa(StrEnum):
    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"


class Prioridade(StrEnum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class TipoTarefa(StrEnum):
    SIMPLES = "simples"
    REPETIDA = "repetida"
    META_MENSAL = "meta_mensal"
