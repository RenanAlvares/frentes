"""tarefas

Revision ID: fc4ca48ac6e6
Revises: d3e60b08b130
Create Date: 2026-10-16 12:24:44.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "fc4ca48ac6e6"
down_revision: str | Sequence[str] | None = "d3e60b08b130"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUS = ("pendente", "em_andamento", "concluida")
PRIORIDADES = ("baixa", "media", "alta")
TIPOS = ("simples", "repetida", "meta_mensal")

# RN-21 (03-dados, CHECK tipo_campos). `IS NOT NULL` na meta: NULL BETWEEN ... dá NULL,
# e a CHECK só rejeita FALSE.
TIPO_CAMPOS = (
    "(tipo = 'simples' AND recorrencia IS NULL AND meta_mensal IS NULL) OR "
    "(tipo = 'repetida' AND prazo IS NOT NULL AND recorrencia IS NOT NULL "
    "AND meta_mensal IS NULL) OR "
    "(tipo = 'meta_mensal' AND prazo IS NULL AND recorrencia IS NULL "
    "AND meta_mensal IS NOT NULL AND meta_mensal BETWEEN 1 AND 31)"
)


def _em(coluna: str, valores: tuple[str, ...]) -> str:
    return f"{coluna} IN ({', '.join(repr(valor) for valor in valores)})"


def _enum(valores: tuple[str, ...], nome: str) -> sa.Enum:
    # Sem a CHECK automática: uma CHECK explícita por coluna, com nome estável.
    return sa.Enum(*valores, name=nome, native_enum=False, length=20)


def upgrade() -> None:
    op.create_table(
        "tarefas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("projeto_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("status", _enum(STATUS, "statustarefa"), nullable=False),
        sa.Column("prioridade", _enum(PRIORIDADES, "prioridade"), nullable=False),
        sa.Column("tipo", _enum(TIPOS, "tipotarefa"), nullable=False),
        sa.Column("prazo", sa.Date(), nullable=True),
        sa.Column("recorrencia", sa.JSON(), nullable=True),
        sa.Column("meta_mensal", sa.Integer(), nullable=True),
        sa.Column("posicao", sa.Integer(), nullable=False),
        sa.Column("concluida_em", sa.DateTime(), nullable=True),
        sa.Column("busca", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(), nullable=True),
        sa.CheckConstraint(_em("status", STATUS), name=op.f("ck_tarefas_statustarefa")),
        sa.CheckConstraint(_em("prioridade", PRIORIDADES), name=op.f("ck_tarefas_prioridade")),
        sa.CheckConstraint(_em("tipo", TIPOS), name=op.f("ck_tarefas_tipotarefa")),
        sa.CheckConstraint(TIPO_CAMPOS, name=op.f("ck_tarefas_tipo_campos")),
        sa.ForeignKeyConstraint(
            ["projeto_id"],
            ["projetos.id"],
            name=op.f("fk_tarefas_projeto_id_projetos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tarefas")),
    )
    op.create_index(
        "ix_tarefas_projeto_id_status_posicao", "tarefas", ["projeto_id", "status", "posicao"]
    )
    op.create_index("ix_tarefas_prazo", "tarefas", ["prazo"])

    op.create_table(
        "tarefa_execucoes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tarefa_id", sa.Uuid(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("prazo_referencia", sa.Date(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tarefa_id"],
            ["tarefas.id"],
            name=op.f("fk_tarefa_execucoes_tarefa_id_tarefas"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tarefa_execucoes")),
    )
    op.create_index("ix_tarefa_execucoes_tarefa_id_data", "tarefa_execucoes", ["tarefa_id", "data"])


def downgrade() -> None:
    op.drop_index("ix_tarefa_execucoes_tarefa_id_data", table_name="tarefa_execucoes")
    op.drop_table("tarefa_execucoes")
    op.drop_index("ix_tarefas_prazo", table_name="tarefas")
    op.drop_index("ix_tarefas_projeto_id_status_posicao", table_name="tarefas")
    op.drop_table("tarefas")
