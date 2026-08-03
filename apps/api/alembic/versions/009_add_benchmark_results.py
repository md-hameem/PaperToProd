"""Add benchmark_results to jobs

Revision ID: 009
Revises: 008
Create Date: 2026-08-03 12:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # We are using sqlite in tests and pg in prod.
    # JSON is supported nicely via sa.JSON
    op.add_column("jobs", sa.Column("benchmark_results", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "benchmark_results")
