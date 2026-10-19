"""Casos de uso de tarefas: simples, repetidas e metas mensais (RN-20..27, RN-90)."""

import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.enums import Prioridade, StatusProjeto, StatusTarefa, TipoTarefa
from app.domain.metas import SituacaoMeta, mes_de, situacao_meta
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
    TarefaHoje,
    TarefaMover,
    TarefasHoje,
)

LIMITE_CONCLUIDAS = 20
HISTORICO_REPETIDA = 5  # 04-api, TarefaDetalhe
SITUACAO_VAZIA = SituacaoMeta(progresso=0, atingida_em=None)


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


def _execucoes_do_mes(
    sessao: Session, tarefas: list[TarefaModelo], hoje: date
) -> dict[uuid.UUID, list[TarefaExecucao]]:
    metas = [t.id for t in tarefas if t.tipo == TipoTarefa.META_MENSAL]
    return repositorio.execucoes_no_periodo(sessao, metas, *mes_de(hoje))


def _situacoes(
    sessao: Session, tarefas: list[TarefaModelo], hoje: date
) -> dict[uuid.UUID, SituacaoMeta]:
    """RN-24 para as metas da lista, numa consulta só."""
    por_meta = _execucoes_do_mes(sessao, tarefas, hoje)
    return {
        tarefa.id: situacao_meta(
            tarefa.meta_mensal or 1, [e.criado_em for e in por_meta[tarefa.id]]
        )
        for tarefa in tarefas
        if tarefa.id in por_meta
    }


def _meta_atingida(tarefa: TarefaModelo, situacoes: dict[uuid.UUID, SituacaoMeta]) -> bool:
    situacao = situacoes.get(tarefa.id)
    return situacao is not None and situacao.atingida_em is not None


def _atrasada(tarefa: TarefaModelo, projeto: ProjetoModelo, hoje: date) -> bool:
    # RN-27: só simples e repetidas (metas não têm prazo).
    return (
        tarefa.tipo in (TipoTarefa.SIMPLES, TipoTarefa.REPETIDA)
        and tarefa.status != StatusTarefa.CONCLUIDA
        and tarefa.prazo is not None
        and tarefa.prazo < hoje
        and projeto.status != StatusProjeto.CONCLUIDO
    )


def _campos(
    tarefa: TarefaModelo, projeto: ProjetoModelo, hoje: date, situacao: SituacaoMeta | None
) -> dict[str, object]:
    colunas = {coluna.key: getattr(tarefa, coluna.key) for coluna in tarefa.__table__.columns}
    calculados: dict[str, object] = {
        "atrasada": _atrasada(tarefa, projeto, hoje),
        # RN-35: o texto oficial da regra vem daqui.
        "recorrencia_descricao": (
            descrever(_regra(tarefa)) if tarefa.tipo == TipoTarefa.REPETIDA else None
        ),
        "progresso_mes": None,
    }
    if tarefa.tipo == TipoTarefa.META_MENSAL:
        # RN-24: no banco a meta é sempre pendente; a API devolve a coluna derivada.
        meta = situacao or SITUACAO_VAZIA
        atingida = meta.atingida_em is not None
        calculados |= {
            "progresso_mes": meta.progresso,
            "status": StatusTarefa.CONCLUIDA if atingida else StatusTarefa.PENDENTE,
            # Posição na coluna Concluída: quando a meta foi atingida no mês.
            "concluida_em": meta.atingida_em,
        }
    return {**colunas, **calculados}


def _resposta(sessao: Session, tarefa: TarefaModelo, projeto: ProjetoModelo, hoje: date) -> Tarefa:
    situacao = _situacoes(sessao, [tarefa], hoje).get(tarefa.id)
    return Tarefa.model_validate(_campos(tarefa, projeto, hoje, situacao))


def _validar_tipo_campos(
    tipo: TipoTarefa, prazo: date | None, recorrencia: object, meta_mensal: object
) -> None:
    """RN-21, sobre o estado final (na edição, o enviado junto com o que já está gravado)."""
    campos = {}
    if tipo == TipoTarefa.META_MENSAL:
        if meta_mensal is None:
            campos["meta_mensal"] = "Informe quantas vezes por mês."
        if prazo is not None:
            campos["prazo"] = "Meta mensal não tem prazo."
        if recorrencia is not None:
            campos["recorrencia"] = "Meta mensal não tem repetição."
    else:
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


def _coluna(
    sessao: Session, projeto_id: uuid.UUID, status: StatusTarefa, hoje: date
) -> list[TarefaModelo]:
    """A coluna como aparece no quadro: metas atingidas saem de Pendente (vão para Concluída)."""
    tarefas = repositorio.da_coluna(sessao, projeto_id, status)
    if status != StatusTarefa.PENDENTE:
        return tarefas
    situacoes = _situacoes(sessao, tarefas, hoje)
    return [t for t in tarefas if not _meta_atingida(t, situacoes)]


def _renumerar(coluna: list[TarefaModelo]) -> None:
    for posicao, tarefa in enumerate(coluna):
        tarefa.posicao = posicao


def _mover(
    sessao: Session,
    tarefa: TarefaModelo,
    destino: StatusTarefa,
    indice: int,
    agora: datetime,
    hoje: date,
) -> None:
    """RN-25: tira da coluna de origem, insere no destino e renumera as duas (0 a n-1)."""
    origem = tarefa.status
    if origem != StatusTarefa.CONCLUIDA:
        resto = [t for t in _coluna(sessao, tarefa.projeto_id, origem, hoje) if t is not tarefa]
        _renumerar(resto)
    # RN-22
    if destino == StatusTarefa.CONCLUIDA and origem != StatusTarefa.CONCLUIDA:
        tarefa.concluida_em = agora
    elif destino != StatusTarefa.CONCLUIDA:
        tarefa.concluida_em = None
    tarefa.status = destino
    if destino != StatusTarefa.CONCLUIDA:
        # Concluída é ordenada por `concluida_em`; lá a posição é ignorada.
        coluna = [t for t in _coluna(sessao, tarefa.projeto_id, destino, hoje) if t is not tarefa]
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
        _mover(sessao, tarefa, StatusTarefa.PENDENTE, 0, agora, hoje)
    tarefa.atualizado_em = agora


def _remover_ultima_do_mes(sessao: Session, tarefa: TarefaModelo, clock: Clock) -> None:
    """RN-24 "-1": apaga a execução mais recente do mês de hoje."""
    do_mes = _execucoes_do_mes(sessao, [tarefa], clock.hoje())[tarefa.id]
    if not do_mes:
        raise Conflito("Não há execuções neste mês.")
    sessao.delete(max(do_mes, key=lambda e: (e.data, e.criado_em)))
    tarefa.atualizado_em = clock.agora_utc()


def obter_quadro(sessao: Session, clock: Clock, projeto_id: uuid.UUID) -> Quadro:
    projeto = _buscar_projeto(sessao, projeto_id)
    hoje = clock.hoje()
    pendentes = repositorio.da_coluna(sessao, projeto_id, StatusTarefa.PENDENTE)
    situacoes = _situacoes(sessao, pendentes, hoje)
    atingidas = [t for t in pendentes if _meta_atingida(t, situacoes)]
    concluidas = repositorio.concluidas(sessao, projeto_id, LIMITE_CONCLUIDAS)

    def resposta(tarefa: TarefaModelo) -> Tarefa:
        return Tarefa.model_validate(_campos(tarefa, projeto, hoje, situacoes.get(tarefa.id)))

    # RN-24/25: metas atingidas entram na Concluída pela data em que foram atingidas.
    concluida = sorted(
        [resposta(t) for t in concluidas + atingidas],
        key=lambda t: (t.concluida_em, t.criado_em),
        reverse=True,
    )[:LIMITE_CONCLUIDAS]
    return Quadro(
        pendente=[resposta(t) for t in pendentes if t not in atingidas],
        em_andamento=[
            resposta(t)
            for t in repositorio.da_coluna(sessao, projeto_id, StatusTarefa.EM_ANDAMENTO)
        ],
        concluida=concluida,
        total_concluidas=repositorio.contar_concluidas(sessao, projeto_id) + len(atingidas),
    )


def listar_concluidas(sessao: Session, clock: Clock, projeto_id: uuid.UUID) -> list[Tarefa]:
    """ "Ver todas" da coluna Concluída (com as metas atingidas no mês)."""
    projeto = _buscar_projeto(sessao, projeto_id)
    hoje = clock.hoje()
    pendentes = repositorio.da_coluna(sessao, projeto_id, StatusTarefa.PENDENTE)
    situacoes = _situacoes(sessao, pendentes, hoje)
    todas = repositorio.concluidas(sessao, projeto_id) + [
        t for t in pendentes if _meta_atingida(t, situacoes)
    ]
    respostas = [
        Tarefa.model_validate(_campos(t, projeto, hoje, situacoes.get(t.id))) for t in todas
    ]
    return sorted(respostas, key=lambda t: (t.concluida_em, t.criado_em), reverse=True)


def obter_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> TarefaDetalhe:
    tarefa = _buscar(sessao, tarefa_id)
    projeto = _buscar_projeto(sessao, tarefa.projeto_id)
    hoje = clock.hoje()
    # 04-api: repetida, as últimas 5 execuções; meta, as do mês; simples não tem.
    historico: list[TarefaExecucao] = []
    if tarefa.tipo == TipoTarefa.REPETIDA:
        historico = repositorio.execucoes(sessao, tarefa.id, HISTORICO_REPETIDA)
    elif tarefa.tipo == TipoTarefa.META_MENSAL:
        historico = _execucoes_do_mes(sessao, [tarefa], hoje)[tarefa.id][::-1]
    situacao = _situacoes(sessao, [tarefa], hoje).get(tarefa.id)
    execucoes = [{"data": e.data, "criado_em": e.criado_em} for e in historico]
    return TarefaDetalhe.model_validate(
        {**_campos(tarefa, projeto, hoje, situacao), "execucoes": execucoes}
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
    return _resposta(sessao, tarefa, projeto, clock.hoje())


def atualizar_tarefa(
    sessao: Session, clock: Clock, tarefa_id: uuid.UUID, dados: TarefaAtualizar
) -> Tarefa:
    tarefa = _buscar(sessao, tarefa_id)
    projeto = _buscar_projeto(sessao, tarefa.projeto_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    if dados.recorrencia is not None:
        alteracoes["recorrencia"] = dados.recorrencia.model_dump(mode="json")
    tipo = alteracoes.get("tipo", tarefa.tipo)
    # RN-21: o tipo pode mudar; valida o novo estado. As execuções já registradas ficam.
    _validar_tipo_campos(
        tipo,
        alteracoes.get("prazo", tarefa.prazo),
        alteracoes.get("recorrencia", tarefa.recorrencia),
        alteracoes.get("meta_mensal", tarefa.meta_mensal),
    )
    pediu_status = "status" in alteracoes
    if pediu_status and tipo == TipoTarefa.META_MENSAL:
        # 04-api / RN-24: a coluna de uma meta vem das execuções do mês.
        raise Conflito("O status de uma meta mensal vem das execuções do mês; use +1 e -1.")
    agora = clock.agora_utc()
    hoje = clock.hoje()
    novo_status = alteracoes.pop("status", tarefa.status)
    for campo, valor in alteracoes.items():
        setattr(tarefa, campo, valor)
    if pediu_status and novo_status == StatusTarefa.CONCLUIDA and tipo == TipoTarefa.REPETIDA:
        # 04-api: PATCH de repetida para Concluída equivale a concluir.
        _concluir_repetida(sessao, tarefa, hoje, agora)
    elif not pediu_status and (
        (tipo == TipoTarefa.REPETIDA and tarefa.status == StatusTarefa.CONCLUIDA)
        or (tipo == TipoTarefa.META_MENSAL and tarefa.status != StatusTarefa.PENDENTE)
    ):
        # Virou repetida ou meta: repetida nunca fica em Concluída (RN-23) e meta é sempre
        # pendente no banco (RN-24); entra no topo de Pendente.
        _mover(sessao, tarefa, StatusTarefa.PENDENTE, 0, agora, hoje)
    elif novo_status != tarefa.status:
        # Mudar o status pela edição põe a tarefa no topo da nova coluna.
        _mover(sessao, tarefa, novo_status, 0, agora, hoje)
    tarefa.busca = normalizar_busca(tarefa.titulo, tarefa.descricao)
    tarefa.atualizado_em = agora
    sessao.commit()
    return _resposta(sessao, tarefa, projeto, hoje)


def excluir_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> None:
    # RN-90: exclusão lógica; vai para a lixeira.
    tarefa = _buscar(sessao, tarefa_id)
    tarefa.excluido_em = clock.agora_utc()
    sessao.commit()


def mover_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID, dados: TarefaMover) -> Quadro:
    tarefa = _buscar(sessao, tarefa_id)
    agora = clock.agora_utc()
    hoje = clock.hoje()
    if tarefa.tipo == TipoTarefa.META_MENSAL:
        # RN-24: não troca de coluna; só reordena dentro da coluna em que aparece.
        atingida = _meta_atingida(tarefa, _situacoes(sessao, [tarefa], hoje))
        aparece = StatusTarefa.CONCLUIDA if atingida else StatusTarefa.PENDENTE
        if dados.status != aparece:
            raise Conflito("Meta mensal não muda de coluna; use +1 e -1.")
        if not atingida:
            _mover(sessao, tarefa, StatusTarefa.PENDENTE, dados.indice, agora, hoje)
        # Na Concluída a ordem vem da data em que a meta foi atingida: nada a reordenar.
    elif dados.status == StatusTarefa.CONCLUIDA and tarefa.tipo == TipoTarefa.REPETIDA:
        # Arrastar para Concluída = concluir (RN-23).
        _concluir_repetida(sessao, tarefa, hoje, agora)
    else:
        _mover(sessao, tarefa, dados.status, dados.indice, agora, hoje)
    sessao.commit()
    return obter_quadro(sessao, clock, tarefa.projeto_id)


def concluir_tarefa(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> Tarefa:
    """Simples → Concluída (RN-22); repetida → avança (RN-23); meta → +1 (RN-24)."""
    tarefa = _buscar(sessao, tarefa_id)
    hoje = clock.hoje()
    agora = clock.agora_utc()
    if tarefa.tipo == TipoTarefa.META_MENSAL:
        # Pode passar da meta (ex.: 5/4).
        sessao.add(TarefaExecucao(tarefa_id=tarefa.id, data=hoje, criado_em=agora))
        tarefa.atualizado_em = agora
    elif tarefa.tipo == TipoTarefa.REPETIDA:
        _concluir_repetida(sessao, tarefa, hoje, agora)
    elif tarefa.status == StatusTarefa.CONCLUIDA:
        raise Conflito("A tarefa já está concluída.")
    else:
        _mover(sessao, tarefa, StatusTarefa.CONCLUIDA, 0, agora, hoje)
    sessao.commit()
    return _resposta(sessao, tarefa, _buscar_projeto(sessao, tarefa.projeto_id), hoje)


def remover_ultima_execucao(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> Tarefa:
    """RN-24 "-1" (só metas)."""
    tarefa = _buscar(sessao, tarefa_id)
    if tarefa.tipo != TipoTarefa.META_MENSAL:
        raise Conflito("Só metas mensais têm execuções para remover.")
    _remover_ultima_do_mes(sessao, tarefa, clock)
    sessao.commit()
    return _resposta(sessao, tarefa, _buscar_projeto(sessao, tarefa.projeto_id), clock.hoje())


def desfazer_conclusao(sessao: Session, clock: Clock, tarefa_id: uuid.UUID) -> Tarefa:
    """RN-26. Simples: volta para o topo de Pendente. Repetida: apaga a última execução e
    restaura o prazo de antes dela. Meta: igual a "-1". Sem o que desfazer → 409."""
    tarefa = _buscar(sessao, tarefa_id)
    agora = clock.agora_utc()
    hoje = clock.hoje()
    if tarefa.tipo == TipoTarefa.META_MENSAL:
        _remover_ultima_do_mes(sessao, tarefa, clock)
    elif tarefa.tipo == TipoTarefa.REPETIDA:
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
        _mover(sessao, tarefa, StatusTarefa.PENDENTE, 0, agora, hoje)
    sessao.commit()
    return _resposta(sessao, tarefa, _buscar_projeto(sessao, tarefa.projeto_id), hoje)


_ORDEM_PRIORIDADE = {Prioridade.ALTA: 0, Prioridade.MEDIA: 1, Prioridade.BAIXA: 2}


def _ordem_hoje(tarefa: TarefaHoje) -> tuple[int, str, str]:
    # RN-62: prioridade (alta, média, baixa), nome do projeto e título, sem diferenciar maiúsculas.
    return (
        _ORDEM_PRIORIDADE[tarefa.prioridade],
        tarefa.projeto.nome.casefold(),
        tarefa.titulo.casefold(),
    )


def listar_hoje(sessao: Session, clock: Clock) -> TarefasHoje:
    """RN-60/61: só projetos ativos; atrasadas são as de RN-27; metas no último dia do mês."""
    hoje = clock.hoje()
    projetos = {p.id: p for p in repositorio_projetos.listar(sessao, arquivados=False)}
    tarefas = repositorio.nao_concluidas_dos_projetos(sessao, list(projetos))
    situacoes = _situacoes(sessao, tarefas, hoje)
    ultimo_dia = hoje == mes_de(hoje)[1]

    def resposta(tarefa: TarefaModelo) -> TarefaHoje:
        projeto = projetos[tarefa.projeto_id]
        campos = _campos(tarefa, projeto, hoje, situacoes.get(tarefa.id))
        ref = {"id": projeto.id, "nome": projeto.nome, "cor": projeto.cor}
        return TarefaHoje.model_validate({**campos, "projeto": ref})

    atrasadas: list[TarefaHoje] = []
    de_hoje: list[TarefaHoje] = []
    for tarefa in tarefas:
        if tarefa.tipo == TipoTarefa.META_MENSAL:
            if ultimo_dia and not _meta_atingida(tarefa, situacoes):
                de_hoje.append(resposta(tarefa))
        elif tarefa.prazo == hoje:
            de_hoje.append(resposta(tarefa))
        elif tarefa.prazo is not None and tarefa.prazo < hoje:
            atrasadas.append(resposta(tarefa))
    return TarefasHoje(
        # RN-62: nas atrasadas, o prazo mais antigo vem primeiro.
        atrasadas=sorted(atrasadas, key=lambda t: (t.prazo or hoje, *_ordem_hoje(t))),
        hoje=sorted(de_hoje, key=_ordem_hoje),
    )
