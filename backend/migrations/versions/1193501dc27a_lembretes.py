"""lembretes

Revision ID: 1193501dc27a
Revises: fc4ca48ac6e6
Create Date: 2026-10-16 18:40:12.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1193501dc27a"
down_revision: str | Sequence[str] | None = "fc4ca48ac6e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lembretes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("projeto_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=False),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("antecedencia_dias", sa.Integer(), nullable=False),
        sa.Column("recorrencia", sa.JSON(), nullable=True),
        sa.Column("concluido_em", sa.DateTime(), nullable=True),
        sa.Column("busca", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(), nullable=True),
        # RN-40
        sa.CheckConstraint(
            "antecedencia_dias BETWEEN 0 AND 60", name=op.f("ck_lembretes_antecedencia")
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"],
            ["projetos.id"],
            name=op.f("fk_lembretes_projeto_id_projetos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lembretes")),
    )
    op.create_index("ix_lembretes_projeto_id", "lembretes", ["projeto_id"])
    op.create_index("ix_lembretes_vencimento", "lembretes", ["vencimento"])

    op.create_table(
        "lembrete_baixas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lembrete_id", sa.Uuid(), nullable=False),
        sa.Column("ocorrencia", sa.Date(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lembrete_id"],
            ["lembretes.id"],
            name=op.f("fk_lembrete_baixas_lembrete_id_lembretes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lembrete_baixas")),
    )
    op.create_index(
        "ix_lembrete_baixas_lembrete_id_criado_em", "lembrete_baixas", ["lembrete_id", "criado_em"]
    )


def downgrade() -> None:
    op.drop_index("ix_lembrete_baixas_lembrete_id_criado_em", table_name="lembrete_baixas")
    op.drop_table("lembrete_baixas")
    op.drop_index("ix_lembretes_vencimento", table_name="lembretes")
    op.drop_index("ix_lembretes_projeto_id", table_name="lembretes")
    op.drop_table("lembretes")
