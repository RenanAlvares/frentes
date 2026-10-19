"""documentos

Revision ID: 6874410533e2
Revises: 1193501dc27a
Create Date: 2026-10-19 12:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6874410533e2"
down_revision: str | Sequence[str] | None = "1193501dc27a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documentos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("projeto_id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("extensao", sa.String(length=20), nullable=False),
        sa.Column("mime", sa.String(length=100), nullable=False),
        sa.Column("tamanho_bytes", sa.BigInteger(), nullable=False),
        sa.Column("chave_storage", sa.String(length=200), nullable=False),
        sa.Column("busca", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("excluido_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["projeto_id"],
            ["projetos.id"],
            name=op.f("fk_documentos_projeto_id_projetos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documentos")),
        sa.UniqueConstraint("chave_storage", name=op.f("uq_documentos_chave_storage")),
    )
    op.create_index("ix_documentos_projeto_id_criado_em", "documentos", ["projeto_id", "criado_em"])


def downgrade() -> None:
    op.drop_index("ix_documentos_projeto_id_criado_em", table_name="documentos")
    op.drop_table("documentos")
