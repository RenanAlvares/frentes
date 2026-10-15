"""configuracoes

Revision ID: e4abb3bb895a
Revises:
Create Date: 2026-10-15 13:56:09.367682+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4abb3bb895a"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "configuracoes",
        sa.Column("chave", sa.String(length=50), nullable=False),
        sa.Column("valor", sa.JSON(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("chave", name=op.f("pk_configuracoes")),
    )


def downgrade() -> None:
    op.drop_table("configuracoes")
