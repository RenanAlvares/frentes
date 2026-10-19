"""Casos de uso de documentos (RN-70..73, RN-90)."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.clock import Clock
from app.domain.documentos import (
    abre_no_navegador,
    extensao_segura,
    mime_da_extensao,
    nome_renomeado,
)
from app.domain.textos import normalizar_busca
from app.erros import ArquivoGrande, NaoEncontrado, Validacao
from app.models.documento import Documento as DocumentoModelo
from app.repositories import documentos as repositorio
from app.repositories import projetos as repositorio_projetos
from app.schemas.documentos import Documento, DocumentoAtualizar
from app.storage.local import Storage, gerar_chave

NOME_PADRAO = "arquivo"


@dataclass(frozen=True)
class ArquivoEnviado:
    """Um arquivo do upload: o nome que veio do usuário (só para exibir) e o conteúdo."""

    nome: str
    conteudo: BinaryIO


@dataclass(frozen=True)
class ArquivoParaBaixar:
    caminho: Path
    nome: str
    mime: str
    inline: bool


def _resposta(documento: DocumentoModelo) -> Documento:
    colunas = {c.key: getattr(documento, c.key) for c in documento.__table__.columns}
    return Documento.model_validate(
        {**colunas, "abre_no_navegador": abre_no_navegador(documento.extensao)}
    )


def _buscar_projeto(sessao: Session, projeto_id: uuid.UUID) -> None:
    if repositorio_projetos.obter(sessao, projeto_id) is None:
        raise NaoEncontrado("Projeto não encontrado.")


def _buscar(sessao: Session, documento_id: uuid.UUID) -> DocumentoModelo:
    documento = repositorio.obter(sessao, documento_id)
    if documento is None:
        raise NaoEncontrado("Documento não encontrado.")
    return documento


def listar_documentos(sessao: Session, projeto_id: uuid.UUID) -> list[Documento]:
    _buscar_projeto(sessao, projeto_id)
    return [_resposta(d) for d in repositorio.do_projeto(sessao, projeto_id)]


def enviar_documentos(
    sessao: Session,
    clock: Clock,
    storage: Storage,
    projeto_id: uuid.UUID,
    arquivos: Sequence[ArquivoEnviado],
    limite_mb: int,
) -> list[Documento]:
    """RN-70 / 04: limite por arquivo; se um passar, nada daquela requisição fica gravado (413)."""
    _buscar_projeto(sessao, projeto_id)
    agora = clock.agora_utc()
    gravadas: list[str] = []
    documentos: list[DocumentoModelo] = []
    try:
        for arquivo in arquivos:
            # O nome do usuário só é exibido; o caminho vem da chave gerada aqui.
            nome = arquivo.nome.strip()[:255] or NOME_PADRAO
            extensao = extensao_segura(nome)
            chave = gerar_chave(projeto_id, extensao)
            try:
                tamanho = storage.salvar(chave, arquivo.conteudo, limite_mb * 1024 * 1024)
            except ArquivoGrande:
                raise ArquivoGrande(f"“{nome}” passa do limite de {limite_mb} MB.") from None
            gravadas.append(chave)
            documentos.append(
                DocumentoModelo(
                    projeto_id=projeto_id,
                    nome=nome,
                    extensao=extensao,
                    mime=mime_da_extensao(extensao),
                    tamanho_bytes=tamanho,
                    chave_storage=chave,
                    busca=normalizar_busca(nome),
                    criado_em=agora,
                    atualizado_em=agora,
                )
            )
        sessao.add_all(documentos)
        sessao.commit()
    except BaseException:
        sessao.rollback()
        for chave in gravadas:
            storage.apagar(chave)
        raise
    return [_resposta(d) for d in documentos]


def arquivo_do_documento(
    sessao: Session, storage: Storage, documento_id: uuid.UUID
) -> ArquivoParaBaixar:
    documento = _buscar(sessao, documento_id)
    caminho = storage.caminho(documento.chave_storage)
    if not caminho.is_file():
        raise NaoEncontrado("O arquivo deste documento não foi encontrado.")
    return ArquivoParaBaixar(
        caminho=caminho,
        nome=documento.nome,
        mime=documento.mime,
        inline=abre_no_navegador(documento.extensao),
    )


def atualizar_documento(
    sessao: Session, clock: Clock, documento_id: uuid.UUID, dados: DocumentoAtualizar
) -> Documento:
    documento = _buscar(sessao, documento_id)
    nome = nome_renomeado(dados.nome, documento.extensao)
    if len(nome) > 255:
        raise Validacao(campos={"nome": "Use no máximo 255 caracteres, contando a extensão."})
    documento.nome = nome
    documento.busca = normalizar_busca(nome)
    documento.atualizado_em = clock.agora_utc()
    sessao.commit()
    return _resposta(documento)


def excluir_documento(sessao: Session, clock: Clock, documento_id: uuid.UUID) -> None:
    # RN-90: exclusão lógica; o arquivo só sai do disco na purga da lixeira (RN-93).
    documento = _buscar(sessao, documento_id)
    documento.excluido_em = clock.agora_utc()
    sessao.commit()
