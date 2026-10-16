"""Casos de uso de tarefas simples e repetidas (RN-20..23, RN-25..27, RN-90).

Metas mensais (RN-24) entram na fase 2.3.
"""

import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.enums import StatusProjeto, StatusTarefa, TipoTarefa
from app.domain.recorrencia import Recorrencia, avancar, descrever
from app.domain.textos import normalizar_busca
from app.erros import Conflito, NaoEncontrado, Validacao
from app.models.projeto import Projeto as ProjetoModelo
from app.models.tarefa import Tarefa as TarefaModelo
from app.models.tarefa import TarefaExecucao
from app.repositories import projetos as repositorio_projetos
from app.repositories import tarefas as repositorio
from app.schemas.tarefas import (
    Quadro,
    Tarefa,
    TarefaAtualizar,
    TarefaCriar,
    TarefaDetalhe,
    TarefaMover,
)

LIMITE_CONCLUIDAS = 20
HISTORICO_REPETIDA = 5  # 04-api, TarefaDetalhe


def _buscar_projeto(sessao: Session, projeto_id: uuid.UUID) -> ProjetoModelo:
    projeto = repositorio_projetos.obter(sessao, projeto_id)
    if projeto is None:
        raise NaoEncontrado("Projeto não encontrado.")
    return projeto


def _buscar(sessao: Session, tarefa_id: uuid.UUID) -> TarefaModelo:
    tarefa = repositorio.obter(sessao, tarefa_id)
    if tarefa is None:
        raise NaoEncontrado("Tarefa não encontrada.")
    return tarefa


def _regra(tarefa: TarefaModelo) -> Recorrencia:
    # O CHECK tipo_campos garante a regra (e o prazo) de toda repetida.
    return Recorrencia.model_validate(tarefa.recorrencia)


def _atrasada(tarefa: TarefaModelo, projeto: ProjetoModelo, hoje: date) -> bool:
    # RN-27 (excluídas e de projeto excluído nem chegam aqui).
    return (
        tarefa.tipo in (TipoTarefa.SIMPLES, TipoTarefa.REPETIDA)
        and tarefa.status != StatusTarefa.CONCLUIDA
        and tarefa.prazo is not None
        and tarefa.prazo < hoje
        and projeto.status != StatusProjeto.CONCLUIDO
    )


def _campos(tarefa: TarefaModelo, projeto: ProjetoModelo, hoje: date) -> dict[str, object]:
    colunas = {coluna.key: getattr(tarefa, coluna.key) for coluna in tarefa.__table__.columns}
    repetida = tarefa.tipo == TipoTarefa.REPETIDA
    calculados = {
        "atrasada": _atrasada(tarefa, projeto, hoje),
        # RN-35: o texto oficial da regra vem daqui.
        "recorrencia_descricao": descrever(_regra(tarefa)) if repetida else None,
        # progresso_mes (metas) entra na fase 2.3.
        "progresso_mes": None,
    }
    return {**colunas, **calculados}


def _resposta(tarefa: TarefaModelo, projeto: ProjetoModelo, hoje: date) -> Tarefa:
    return Tarefa.model_validate(_campos(tarefa, projeto, hoje))


def _validar_tipo_campos(
    tipo: TipoTarefa, prazo: date | None, recorrencia: object, meta_mensal: object
) -> None:
    """RN-21, sobre o estado final (na edição, o enviado junto com o que já está gravado)."""
    campos = {}
    if tipo == TipoTarefa.SIMPLES and recorrencia is not None:
        campos["recorrencia"] = "Tarefa simples não tem repetição."
    if tipo == TipoTarefa.REPETIDA:
        if prazo is None:
            campos["prazo"] = "Informe a primeira data."
        if recorrencia is None:
            campos["recorrencia"] = "Informe a repetição."
    if meta_mensal is not None:
        nome = "simples" if tipo == TipoTarefa.SIMPLES else "repetida"
        campos["meta_mensal"] = f"Tarefa {nome} não tem meta mensal."
    if campos:
        raise Validacao(campos=campos)


def _renumerar(coluna: list[TarefaModelo]) -> None:
    for posicao, tarefa in enumerate(coluna):
        tarefa.posicao = posicao


def _mover(
    sessao: Session, tarefa: TarefaModelo, destino: StatusTarefa, indice: int, agora: datetime
) -> None:
    """RN-25: tira da coluna de origem, insere no destino e renumera as duas (0 a n-1)."""
    origem = tarefa.status
    if origem != StatusTarefa.CONCLUIDA:
        resto = [
            t for t in repositorio.da_coluna(sessao, tarefa.projeto_id, origem) if t is not tarefa
        ]
        _renumerar(resto)
    # RN-22
    if destino == StatusTarefa.CONCLUIDA and origem != StatusTarefa.CONCLUIDA:
        tarefa.concluida_em = agora
    elif destino != StatusTarefa.CONCLUIDA:
        tarefa.concluida_em = None
    tarefa.status = destino
    if destino != StatusTarefa.CONCLUIDA:
        # Concluída é ordenada por `concluida_em`; lá a posição é ignorada.
        coluna = [
            t for t in repositorio.da_coluna(sessao, tarefa.projeto_id, destino) if t is not tarefa
        ]
        coluna.insert(min(indice, len(coluna)), tarefa)
        _renumerar(coluna)
    tarefa.atualizado_em = agora


def _concluir_repetida(sessao: Session, tarefa: TarefaModelo, hoje: date, agora: datetime) -> None:
    """RN-23: registra a execução, avança o prazo e fica em Pendente (nunca em Concluída)."""
    atual = tarefa.prazo
    assert atual is not None  # CHECK tipo_campos
    sessao.add(
        TarefaExecucao(tarefa_id=tarefa.id, data=hoje, prazo_referencia=atual, criado_em=agora)
    )
    tarefa.prazo = avancar(_regra(tarefa), atual, hoje)
    if tarefa.status != StatusTarefa.PENDENTE:
        # Vinda de Em andamento, entra no topo de Pendente; já pendente, fica onde está.
        _mover(sessao, tarefa, StatusTarefa.PENDENTE, 0, agora)
    tarefa.atualizado_em = agora


def _concluir(sessao: Session, clock: Clock, tarefa: TarefaModelo, indice: int = 0) -> None:
    """Concluir por botão, edição ou arraste para Concluída: o efeito depende do tipo."""
    if tarefa.tipo == TipoTarefa.REPETIDA:
        _concluir_repetida(sessao, tarefa, clock.hoje(), clock.agora_utc())
    else:
        _mover(sessao, tarefa, StatusTarefa.CONCLUIDA, indice, clock.agora_utc())


def obter_quadro(sessao: Session, clock: Clock, projeto_id: uuid.UUID) -> Quadro:
    projeto = _buscar_projeto(sessao, projeto_id)
    hoje = clock.hoje()

    def lista(tarefas: list[TarefaModelo]) -> list[Tarefa]:
        return [_resposta(tarefa, projeto, hoje) for tarefa in tarefas]

    return Quadro(
        pendente=lista(repositorio.da_coluna(sessao, projeto_id, StatusTarefa.PENDENTE)),
        em_andamento=lista(repositorio.da_coluna(sessao, projeto_id, StatusTarefa.EM_ANDAMENTO)),
        concluida=lista(repositorio.concluidas(sessao, projeto_id, LIMITE_CONCLUIDAS)),
        total_concluidas=repositorio.contar_concluidas(sessao, projeto_id),
    )


def listar_concluidas(sessao: Session, clock: Clock, projeto_id: uuid.UUID) -> list[Tarefa]:
    """ "Ver todas" da coluna Concluída."""
    projeto = _buscar_projeto(sessao, projeto_id)
    hoje = clock.hoje()
    return [_resposta(t, projeto, hoje) for t in repositorio.concluidas(sessao, projeto_id)]


def obter_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> TarefaDetalhe:
    tarefa = _buscar(sessao, tarefa_id)
    projeto = _buscar_projeto(sessao, tarefa.projeto_id)
    # Repetida: as últimas 5 execuções. Simples não tem; as metas entram na fase 2.3.
    historico = (
        repositorio.execucoes(sessao, tarefa.id, HISTORICO_REPETIDA)
        if tarefa.tipo == TipoTarefa.REPETIDA
        else []
    )
    execucoes = [{"data": e.data, "criado_em": e.criado_em} for e in historico]
    return TarefaDetalhe.model_validate(
        {**_campos(tarefa, projeto, clock.hoje()), "execucoes": execucoes}
    )


def criar_tarefa(
    sessao: Session, clock: Clock, projeto_id: uuid.UUID, dados: TarefaCriar
) -> Tarefa:
    projeto = _buscar_projeto(sessao, projeto_id)
    _validar_tipo_campos(dados.tipo, dados.prazo, dados.recorrencia, dados.meta_mensal)
    agora = clock.agora_utc()
    pendentes = repositorio.da_coluna(sessao, projeto_id, StatusTarefa.PENDENTE)
    tarefa = TarefaModelo(
        **dados.model_dump(exclude={"recorrencia"}),
        recorrencia=dados.recorrencia.model_dump(mode="json") if dados.recorrencia else None,
        projeto_id=projeto_id,
        status=StatusTarefa.PENDENTE,
        # RN-25: entra no topo de Pendente.
        posicao=pendentes[0].posicao - 1 if pendentes else 0,
        busca=normalizar_busca(dados.titulo, dados.descricao),
        criado_em=agora,
        atualizado_em=agora,
    )
    sessao.add(tarefa)
    sessao.commit()
    return _resposta(tarefa, projeto, clock.hoje())


def atualizar_tarefa(
    sessao: Session, clock: Clock, tarefa_id: uuid.UUID, dados: TarefaAtualizar
) -> Tarefa:
    tarefa = _buscar(sessao, tarefa_id)
    projeto = _buscar_projeto(sessao, tarefa.projeto_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    if dados.recorrencia is not None:
        alteracoes["recorrencia"] = dados.recorrencia.model_dump(mode="json")
    # RN-21: o tipo pode mudar; valida o novo estado. As execuções já registradas ficam.
    _validar_tipo_campos(
        alteracoes.get("tipo", tarefa.tipo),
        alteracoes.get("prazo", tarefa.prazo),
        alteracoes.get("recorrencia", tarefa.recorrencia),
        alteracoes.get("meta_mensal", tarefa.meta_mensal),
    )
    agora = clock.agora_utc()
    pediu_status = "status" in alteracoes
    novo_status = alteracoes.pop("status", tarefa.status)
    for campo, valor in alteracoes.items():
        setattr(tarefa, campo, valor)
    repetida = tarefa.tipo == TipoTarefa.REPETIDA
    if pediu_status and novo_status == StatusTarefa.CONCLUIDA and repetida:
        # 04-api: PATCH de repetida para Concluída equivale a concluir.
        _concluir_repetida(sessao, tarefa, clock.hoje(), agora)
    elif repetida and tarefa.status == StatusTarefa.CONCLUIDA:
        # Simples concluída que virou repetida: repetida nunca fica em Concluída (RN-23).
        _mover(sessao, tarefa, StatusTarefa.PENDENTE, 0, agora)
    elif novo_status != tarefa.status:
        # Mudar o status pela edição põe a tarefa no topo da nova coluna.
        _mover(sessao, tarefa, novo_status, 0, agora)
    tarefa.busca = normalizar_busca(tarefa.titulo, tarefa.descricao)
    tarefa.atualizado_em = agora
    sessao.commit()
    return _resposta(tarefa, projeto, clock.hoje())


def excluir_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> None:
    # RN-90: exclusão lógica; vai para a lixeira.
    tarefa = _buscar(sessao, tarefa_id)
    tarefa.excluido_em = clock.agora_utc()
    sessao.commit()


def mover_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID, dados: TarefaMover) -> Quadro:
    tarefa = _buscar(sessao, tarefa_id)
    if dados.status == StatusTarefa.CONCLUIDA:
        # Arrastar para Concluída = concluir (RN-23 para repetidas).
        _concluir(sessao, clock, tarefa, dados.indice)
    else:
        _mover(sessao, tarefa, dados.status, dados.indice, clock.agora_utc())
    sessao.commit()
    return obter_quadro(sessao, clock, tarefa.projeto_id)


def concluir_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> Tarefa:
    tarefa = _buscar(sessao, tarefa_id)
    if tarefa.status == StatusTarefa.CONCLUIDA:
        raise Conflito("A tarefa já está concluída.")
    _concluir(sessao, clock, tarefa)
    sessao.commit()
    return _resposta(tarefa, _buscar_projeto(sessao, tarefa.projeto_id), clock.hoje())


def desfazer_conclusao(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> Tarefa:
    """RN-26. Simples: volta para o topo de Pendente. Repetida: apaga a última execução e
    restaura o prazo de antes dela. Sem o que desfazer → 409."""
    tarefa = _buscar(sessao, tarefa_id)
    agora = clock.agora_utc()
    if tarefa.tipo == TipoTarefa.REPETIDA:
        ultimas = repositorio.execucoes(sessao, tarefa.id, 1)
        if not ultimas:
            raise Conflito("Não há conclusão para desfazer.")
        (ultima,) = ultimas
        # Execução de quando a tarefa era meta não tem prazo de referência: o prazo fica.
        if ultima.prazo_referencia is not None:
            tarefa.prazo = ultima.prazo_referencia
        sessao.delete(ultima)
        tarefa.atualizado_em = agora
    else:
        if tarefa.status != StatusTarefa.CONCLUIDA:
            raise Conflito("Não há conclusão para desfazer.")
        _mover(sessao, tarefa, StatusTarefa.PENDENTE, 0, agora)
    sessao.commit()
    return _resposta(tarefa, _buscar_projeto(sessao, tarefa.projeto_id), clock.hoje())
