"""Add job advanced options

Revision ID: 005_add_job_advanced_options
Revises: 004_add_api_keys
Create Date: 2026-07-31 01:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op  # type: ignore

# revision identifiers, used by Alembic.
revision: str = "005_add_job_advanced_options"
down_revision: str | None = "004_add_api_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("advanced_options", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "advanced_options")
