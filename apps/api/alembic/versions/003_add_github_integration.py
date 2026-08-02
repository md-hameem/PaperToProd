"""Add github integration fields

Revision ID: 003_add_github_integration
Revises: 002_add_billing_fields
Create Date: 2026-07-31 01:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op  # type: ignore

# revision identifiers, used by Alembic.
revision: str = "003_add_github_integration"
down_revision: str | None = "002_add_billing_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workspaces", sa.Column("github_installation_id", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "workspaces", sa.Column("github_account_name", sa.String(length=100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("workspaces", "github_account_name")
    op.drop_column("workspaces", "github_installation_id")
