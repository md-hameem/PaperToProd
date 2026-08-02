"""Add billing fields

Revision ID: 002_add_billing_fields
Revises: 001_initial_schema
Create Date: 2026-07-31 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op  # type: ignore

# revision identifiers, used by Alembic.
revision: str = "002_add_billing_fields"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add billing fields to workspaces
    op.add_column(
        "workspaces",
        sa.Column("subscription_tier", sa.String(length=20), server_default="free", nullable=False),
    )
    op.add_column(
        "workspaces", sa.Column("stripe_customer_id", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "workspaces", sa.Column("stripe_subscription_id", sa.String(length=100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("workspaces", "stripe_subscription_id")
    op.drop_column("workspaces", "stripe_customer_id")
    op.drop_column("workspaces", "subscription_tier")
