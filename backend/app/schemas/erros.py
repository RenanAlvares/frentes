from pydantic import BaseModel


class ErroDetalhe(BaseModel):
    codigo: str
    mensagem: str
    # Só em erros de validação: campo → mensagem em português.
    campos: dict[str, str] | None = None


class ErroResposta(BaseModel):
    erro: ErroDetalhe
