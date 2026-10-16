"""Casos de uso de tarefas simples (RN-20..22, RN-25..27, RN-90).

Repetidas (RN-23) e metas (RN-24) entram nas fases 2.2 e 2.3.
"""

import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.enums import StatusProjeto, StatusTarefa, TipoTarefa
from app.domain.textos import normalizar_busca
from app.erros import Conflito, NaoEncontrado, Validacao
from app.models.projeto import Projeto as ProjetoModelo
from app.models.tarefa import Tarefa as TarefaModelo
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
    # recorrencia_descricao (2.2) e progresso_mes (2.3) só existem para repetidas e metas.
    calculados = {
        "atrasada": _atrasada(tarefa, projeto, hoje),
        "recorrencia_descricao": None,
        "progresso_mes": None,
    }
    return {**colunas, **calculados}


def _resposta(tarefa: TarefaModelo, projeto: ProjetoModelo, hoje: date) -> Tarefa:
    return Tarefa.model_validate(_campos(tarefa, projeto, hoje))


def _validar_tipo_campos(recorrencia: object, meta_mensal: object) -> None:
    # RN-21 para simples: sem repetição e sem meta.
    campos = {}
    if recorrencia is not None:
        campos["recorrencia"] = "Tarefa simples não tem repetição."
    if meta_mensal is not None:
        campos["meta_mensal"] = "Tarefa simples não tem meta mensal."
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
    # Simples não tem execuções; o histórico de repetidas e metas entra na fase 2.
    return TarefaDetalhe.model_validate({**_campos(tarefa, projeto, clock.hoje()), "execucoes": []})


def criar_tarefa(
    sessao: Session, clock: Clock, projeto_id: uuid.UUID, dados: TarefaCriar
) -> Tarefa:
    projeto = _buscar_projeto(sessao, projeto_id)
    _validar_tipo_campos(dados.recorrencia, dados.meta_mensal)
    agora = clock.agora_utc()
    pendentes = repositorio.da_coluna(sessao, projeto_id, StatusTarefa.PENDENTE)
    tarefa = TarefaModelo(
        **dados.model_dump(),
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
    _validar_tipo_campos(
        alteracoes.get("recorrencia", tarefa.recorrencia),
        alteracoes.get("meta_mensal", tarefa.meta_mensal),
    )
    agora = clock.agora_utc()
    novo_status = alteracoes.pop("status", tarefa.status)
    for campo, valor in alteracoes.items():
        setattr(tarefa, campo, valor)
    if novo_status != tarefa.status:
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
    _mover(sessao, tarefa, dados.status, dados.indice, clock.agora_utc())
    sessao.commit()
    return obter_quadro(sessao, clock, tarefa.projeto_id)


def concluir_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> Tarefa:
    tarefa = _buscar(sessao, tarefa_id)
    if tarefa.status == StatusTarefa.CONCLUIDA:
        raise Conflito("A tarefa já está concluída.")
    _mover(sessao, tarefa, StatusTarefa.CONCLUIDA, 0, clock.agora_utc())
    sessao.commit()
    return _resposta(tarefa, _buscar_projeto(sessao, tarefa.projeto_id), clock.hoje())


def desfazer_conclusao(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> Tarefa:
    # RN-26 (simples): volta para o topo de Pendente; sem conclusão → 409.
    tarefa = _buscar(sessao, tarefa_id)
    if tarefa.status != StatusTarefa.CONCLUIDA:
        raise Conflito("Não há conclusão para desfazer.")
    _mover(sessao, tarefa, StatusTarefa.PENDENTE, 0, clock.agora_utc())
    sessao.commit()
    return _resposta(tarefa, _buscar_projeto(sessao, tarefa.projeto_id), clock.hoje())
