"""Casos de uso de lembretes (RN-40..46, RN-90)."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.avisos import atrasadas_do_lembrete, na_janela
from app.domain.enums import StatusProjeto
from app.domain.recorrencia import Recorrencia, avancar, descrever
from app.domain.textos import normalizar_busca
from app.erros import Conflito, NaoEncontrado
from app.models.lembrete import Lembrete as LembreteModelo
from app.models.lembrete import LembreteBaixa
from app.models.projeto import Projeto as ProjetoModelo
from app.repositories import configuracoes as repositorio_configuracoes
from app.repositories import lembretes as repositorio
from app.repositories import projetos as repositorio_projetos
from app.schemas.lembretes import Lembrete, LembreteAtualizar, LembreteCriar, ListaLembretes
from app.services.configuracoes import PADROES

ANTECEDENCIA_PADRAO = "antecedencia_padrao_lembretes"


def _buscar_projeto(sessao: Session, projeto_id: uuid.UUID) -> ProjetoModelo:
    projeto = repositorio_projetos.obter(sessao, projeto_id)
    if projeto is None:
        raise NaoEncontrado("Projeto não encontrado.")
    return projeto


def _buscar(sessao: Session, lembrete_id: uuid.UUID) -> LembreteModelo:
    lembrete = repositorio.obter(sessao, lembrete_id)
    if lembrete is None:
        raise NaoEncontrado("Lembrete não encontrado.")
    return lembrete


def _regra(lembrete: LembreteModelo) -> Recorrencia | None:
    return Recorrencia.model_validate(lembrete.recorrencia) if lembrete.recorrencia else None


def _resposta(lembrete: LembreteModelo, projeto: ProjetoModelo, hoje: date) -> Lembrete:
    regra = _regra(lembrete)
    concluido = lembrete.concluido_em is not None
    # RN-41: ativo = sem baixa definitiva e em projeto ativo (excluídos nem chegam aqui).
    ativo = not concluido and projeto.status != StatusProjeto.CONCLUIDO
    # Mesmas regras dos avisos (domain/avisos.py), para a coluna e o painel concordarem.
    janela = na_janela(lembrete.vencimento, lembrete.antecedencia_dias, hoje)
    atrasadas = 0 if concluido else atrasadas_do_lembrete(regra, lembrete.vencimento, hoje)
    colunas = {c.key: getattr(lembrete, c.key) for c in lembrete.__table__.columns}
    return Lembrete.model_validate(
        {
            **colunas,
            "recorrencia_descricao": descrever(regra) if regra else None,  # RN-35
            "dias_restantes": (lembrete.vencimento - hoje).days,  # RN-03
            "na_janela": ativo and janela,  # RN-42
            "ocorrencias_atrasadas": atrasadas,  # RN-34
        }
    )


def _antecedencia_padrao(sessao: Session) -> int:
    valor = repositorio_configuracoes.valor(sessao, ANTECEDENCIA_PADRAO)
    return valor if isinstance(valor, int) else PADROES[ANTECEDENCIA_PADRAO]


def listar_lembretes(sessao: Session, clock: Clock, projeto_id: uuid.UUID) -> ListaLembretes:
    projeto = _buscar_projeto(sessao, projeto_id)
    hoje = clock.hoje()
    return ListaLembretes(
        ativos=[_resposta(lb, projeto, hoje) for lb in repositorio.ativos(sessao, projeto_id)],
        concluidos=[
            _resposta(lb, projeto, hoje) for lb in repositorio.concluidos(sessao, projeto_id)
        ],
    )


def criar_lembrete(
    sessao: Session, clock: Clock, projeto_id: uuid.UUID, dados: LembreteCriar
) -> Lembrete:
    projeto = _buscar_projeto(sessao, projeto_id)
    agora = clock.agora_utc()
    antecedencia = dados.antecedencia_dias
    lembrete = LembreteModelo(
        projeto_id=projeto_id,
        titulo=dados.titulo,
        observacao=dados.observacao,
        vencimento=dados.vencimento,
        antecedencia_dias=_antecedencia_padrao(sessao) if antecedencia is None else antecedencia,
        recorrencia=dados.recorrencia.model_dump(mode="json") if dados.recorrencia else None,
        busca=normalizar_busca(dados.titulo, dados.observacao),
        criado_em=agora,
        atualizado_em=agora,
    )
    sessao.add(lembrete)
    sessao.commit()
    return _resposta(lembrete, projeto, clock.hoje())


def atualizar_lembrete(
    sessao: Session, clock: Clock, lembrete_id: uuid.UUID, dados: LembreteAtualizar
) -> Lembrete:
    lembrete = _buscar(sessao, lembrete_id)
    projeto = _buscar_projeto(sessao, lembrete.projeto_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    if dados.recorrencia is not None:
        alteracoes["recorrencia"] = dados.recorrencia.model_dump(mode="json")
        # Concluído que ganha repetição volta a ficar ativo: só não recorrentes ficam
        # concluídos (RN-43).
        lembrete.concluido_em = None
    # RN-46: mudar o vencimento muda a âncora da sequência (é só gravar).
    for campo, valor in alteracoes.items():
        setattr(lembrete, campo, valor)
    lembrete.busca = normalizar_busca(lembrete.titulo, lembrete.observacao)
    lembrete.atualizado_em = clock.agora_utc()
    sessao.commit()
    return _resposta(lembrete, projeto, clock.hoje())


def excluir_lembrete(sessao: Session, clock: Clock, lembrete_id: uuid.UUID) -> None:
    # RN-90: exclusão lógica; vai para a lixeira.
    lembrete = _buscar(sessao, lembrete_id)
    lembrete.excluido_em = clock.agora_utc()
    sessao.commit()


def dar_baixa(sessao: Session, clock: Clock, lembrete_id: uuid.UUID) -> Lembrete:
    """RN-43: não recorrente conclui; recorrente registra a ocorrência e avança.
    Vale a qualquer momento, inclusive antes da janela."""
    lembrete = _buscar(sessao, lembrete_id)
    hoje = clock.hoje()
    agora = clock.agora_utc()
    regra = _regra(lembrete)
    if regra:
        sessao.add(
            LembreteBaixa(lembrete_id=lembrete.id, ocorrencia=lembrete.vencimento, criado_em=agora)
        )
        lembrete.vencimento = avancar(regra, lembrete.vencimento, hoje)
    elif lembrete.concluido_em is not None:
        raise Conflito("O lembrete já recebeu baixa.")
    else:
        lembrete.concluido_em = agora
    lembrete.atualizado_em = agora
    sessao.commit()
    return _resposta(lembrete, _buscar_projeto(sessao, lembrete.projeto_id), hoje)


def desfazer_baixa(sessao: Session, clock: Clock, lembrete_id: uuid.UUID) -> Lembrete:
    """RN-44: volta exatamente ao estado anterior. Também é o "Reativar". Sem baixa → 409."""
    lembrete = _buscar(sessao, lembrete_id)
    if _regra(lembrete):
        baixa = repositorio.ultima_baixa(sessao, lembrete.id)
        if baixa is None:
            raise Conflito("Não há baixa para desfazer.")
        lembrete.vencimento = baixa.ocorrencia
        sessao.delete(baixa)
    elif lembrete.concluido_em is None:
        raise Conflito("Não há baixa para desfazer.")
    else:
        lembrete.concluido_em = None
    lembrete.atualizado_em = clock.agora_utc()
    sessao.commit()
    return _resposta(lembrete, _buscar_projeto(sessao, lembrete.projeto_id), clock.hoje())
