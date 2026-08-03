"""Add job public flag for gallery

Revision ID: 007
Revises: 006
Create Date: 2026-08-03 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add is_public column to jobs table
    op.add_column(
        "jobs", sa.Column("is_public", sa.Boolean(), server_default="false", nullable=False)
    )

    # Create index on is_public and fidelity_score for fast gallery querying
    op.create_index("ix_jobs_public", "jobs", ["is_public", "fidelity_score"])


def downgrade() -> None:
    op.drop_index("ix_jobs_public", table_name="jobs")
    op.drop_column("jobs", "is_public")
