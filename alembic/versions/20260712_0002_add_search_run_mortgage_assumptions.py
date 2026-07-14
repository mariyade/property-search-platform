"""add search run mortgage assumptions

Revision ID: 20260712_0002
Revises: 20260706_0001
Create Date: 2026-07-12
"""

import sqlalchemy as sa

from alembic import op

revision = "20260712_0002"
down_revision = "20260706_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "search_runs",
        sa.Column(
            "mortgage_rate",
            sa.Float(),
            nullable=False,
            server_default="0.0515",
        ),
    )
    op.add_column(
        "search_runs",
        sa.Column("ltv", sa.Float(), nullable=False, server_default="0.75"),
    )
    op.alter_column("search_runs", "mortgage_rate", server_default=None)
    op.alter_column("search_runs", "ltv", server_default=None)


def downgrade():
    op.drop_column("search_runs", "ltv")
    op.drop_column("search_runs", "mortgage_rate")
