"""projetos

Revision ID: d3e60b08b130
Revises: e4abb3bb895a
Create Date: 2026-10-15 17:58:40.772658+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d3e60b08b130"
down_revision: str | Sequence[str] | None = "e4abb3bb895a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUS = ("planejado", "em_andamento", "aguardando", "concluido")
CORES = ("azul", "verde", "roxo", "laranja", "rosa", "vermelho", "ciano", "cinza")


def _em(coluna: str, valores: tuple[str, ...]) -> str:
    return f"{coluna} IN ({', '.join(repr(valor) for valor in valores)})"


def upgrade() -> None:
    # Enums sem a CHECK automática: uma CHECK explícita por coluna, com nome estável.
    op.create_table(
        "projetos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(*STATUS, name="statusprojeto", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column(
            "cor",
            sa.Enum(*CORES, name="corprojeto", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("data_inicio", sa.Date(), nullable=True),
        sa.Column("prazo", sa.Date(), nullable=True),
        sa.Column("acompanhar_progresso", sa.Boolean(), nullable=False),
        sa.Column("posicao", sa.Integer(), nullable=False),
        sa.Column("busca", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(), nullable=True),
        sa.CheckConstraint(_em("status", STATUS), name=op.f("ck_projetos_statusprojeto")),
        sa.CheckConstraint(_em("cor", CORES), name=op.f("ck_projetos_corprojeto")),
        # RN-16
        sa.CheckConstraint(
            "data_inicio IS NULL OR prazo IS NULL OR data_inicio <= prazo",
            name=op.f("ck_projetos_datas"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projetos")),
    )
    op.create_index(
        "ix_projetos_excluido_em_status_posicao",
        "projetos",
        ["excluido_em", "status", "posicao"],
    )


def downgrade() -> None:
    op.drop_index("ix_projetos_excluido_em_status_posicao", table_name="projetos")
    op.drop_table("projetos")
