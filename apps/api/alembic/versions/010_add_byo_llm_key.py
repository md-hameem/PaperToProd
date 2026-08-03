"""Add BYO LLM key fields to workspaces

Revision ID: 010
Revises: 009
Create Date: 2026-08-03 14:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workspaces", sa.Column("byo_llm_provider", sa.String(length=50), nullable=True))
    op.add_column(
        "workspaces", sa.Column("byo_llm_api_key_encrypted", sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("workspaces", "byo_llm_api_key_encrypted")
    op.drop_column("workspaces", "byo_llm_provider")
