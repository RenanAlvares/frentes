"""Consultas da busca (RN-121): `LIKE '%termo%'` sobre a coluna `busca`, SQL portátil."""

from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anotacao import Anotacao
from app.models.documento import Documento
from app.models.lembrete import Lembrete
from app.models.projeto import Projeto
from app.models.tarefa import Tarefa

LIMITE = 10  # RN-121: até 10 resultados por tipo.

ItemDeProjeto = Tarefa | Lembrete | Documento | Anotacao


def projetos(sessao: Session, termo: str) -> list[Projeto]:
    """RN-120: inclui os arquivados; nunca os da lixeira."""
    consulta = (
        select(Projeto)
        # `autoescape`: `%` e `_` digitados são texto, não curinga.
        .where(Projeto.excluido_em.is_(None), Projeto.busca.contains(termo, autoescape=True))
        .order_by(Projeto.atualizado_em.desc(), Projeto.busca)
        .limit(LIMITE)
    )
    return list(sessao.scalars(consulta))


def itens(
    sessao: Session, modelo: type[ItemDeProjeto], termo: str
) -> list[tuple[ItemDeProjeto, Projeto]]:
    """Itens fora da lixeira, de projeto fora da lixeira (RN-90/91), com o projeto."""
    consulta = (
        select(modelo, Projeto)
        .join(Projeto, modelo.projeto_id == Projeto.id)
        .where(
            modelo.excluido_em.is_(None),
            Projeto.excluido_em.is_(None),
            modelo.busca.contains(termo, autoescape=True),
        )
        # Mais recentes primeiro; empate pelo texto, para a ordem não variar.
        .order_by(modelo.atualizado_em.desc(), modelo.busca)
        .limit(LIMITE)
    )
    linhas: Any = sessao.execute(consulta)
    return [(cast(ItemDeProjeto, item), cast(Projeto, projeto)) for item, projeto in linhas]
