"""anotacoes

Revision ID: 979fe9663951
Revises: 6874410533e2
Create Date: 2026-10-19 15:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "979fe9663951"
down_revision: str | Sequence[str] | None = "6874410533e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CORES = ("amarelo", "azul", "verde", "rosa", "roxo", "cinza")


def _em(coluna: str, valores: tuple[str, ...]) -> str:
    return f"{coluna} IN ({', '.join(repr(valor) for valor in valores)})"


def upgrade() -> None:
    # Enum sem a CHECK automática: uma CHECK explícita, com nome estável.
    op.create_table(
        "anotacoes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("projeto_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(length=120), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column(
            "cor",
            sa.Enum(*CORES, name="coranotacao", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("fixada", sa.Boolean(), nullable=False),
        sa.Column("busca", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(), nullable=True),
        sa.CheckConstraint(_em("cor", CORES), name=op.f("ck_anotacoes_coranotacao")),
        sa.ForeignKeyConstraint(
            ["projeto_id"],
            ["projetos.id"],
            name=op.f("fk_anotacoes_projeto_id_projetos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_anotacoes")),
    )
    op.create_index(
        "ix_anotacoes_projeto_id_fixada_atualizado_em",
        "anotacoes",
        ["projeto_id", "fixada", "atualizado_em"],
    )


def downgrade() -> None:
    op.drop_index("ix_anotacoes_projeto_id_fixada_atualizado_em", table_name="anotacoes")
    op.drop_table("anotacoes")
