"""Busca global (RN-120..121)."""

from sqlalchemy.orm import Session

from app.domain.enums import StatusProjeto
from app.domain.textos import normalizar_busca, titulo_da_anotacao
from app.erros import Validacao
from app.models.anotacao import Anotacao
from app.models.documento import Documento
from app.models.lembrete import Lembrete
from app.models.projeto import Projeto
from app.models.tarefa import Tarefa
from app.repositories import busca as repositorio
from app.schemas.busca import ItemBusca, ResultadoBusca

MINIMO = 2  # RN-121


def _item(id_: object, titulo: str, projeto: Projeto) -> ItemBusca:
    return ItemBusca.model_validate(
        {
            "id": id_,
            "titulo": titulo,
            "projeto": {"id": projeto.id, "nome": projeto.nome, "cor": projeto.cor},
            "arquivado": projeto.status == StatusProjeto.CONCLUIDO,
        }
    )


def _titulo(item: repositorio.ItemDeProjeto) -> str:
    if isinstance(item, Documento):
        return item.nome
    if isinstance(item, Anotacao):
        return titulo_da_anotacao(item.titulo, item.texto)
    return item.titulo


def buscar(sessao: Session, q: str) -> ResultadoBusca:
    """RN-121: o termo é normalizado como a coluna `busca` (sem acentos nem maiúsculas)."""
    termo = normalizar_busca(q)
    if len(termo) < MINIMO:
        raise Validacao(campos={"q": f"Digite pelo menos {MINIMO} letras para buscar."})

    def do_tipo(modelo: type[repositorio.ItemDeProjeto]) -> list[ItemBusca]:
        return [
            _item(item.id, _titulo(item), projeto)
            for item, projeto in repositorio.itens(sessao, modelo, termo)
        ]

    return ResultadoBusca(
        projetos=[_item(p.id, p.nome, p) for p in repositorio.projetos(sessao, termo)],
        tarefas=do_tipo(Tarefa),
        lembretes=do_tipo(Lembrete),
        anotacoes=do_tipo(Anotacao),
        documentos=do_tipo(Documento),
    )
