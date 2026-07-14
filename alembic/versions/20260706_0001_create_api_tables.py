"""create api tables

Revision ID: 20260706_0001
Revises: None
Create Date: 2026-07-06
"""

import sqlalchemy as sa

from alembic import op

revision = "20260706_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    metadata = sa.MetaData()

    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(), unique=True),
        sa.Column("username", sa.String(), unique=True),
        sa.Column("first_name", sa.String()),
        sa.Column("last_name", sa.String()),
        sa.Column("hashed_password", sa.String()),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("role", sa.String()),
        sa.Column("phone_number", sa.String()),
    )
    users.create(bind, checkfirst=True)

    search_runs = sa.Table(
        "search_runs",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("status", sa.String(), nullable=False, default="pending"),
        sa.Column("search_location", sa.String(), nullable=False),
        sa.Column("location_identifier", sa.String(), nullable=False),
        sa.Column("radius", sa.Float(), nullable=False),
        sa.Column("min_price", sa.Integer()),
        sa.Column("max_price", sa.Integer()),
        sa.Column("min_bedrooms", sa.Integer()),
        sa.Column("max_bedrooms", sa.Integer()),
        sa.Column("property_types", sa.String(), nullable=False),
        sa.Column("include_sstc", sa.String(), nullable=False),
        sa.Column("sort_type", sa.Integer(), nullable=False, default=4),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("transaction_type", sa.String(), nullable=False),
        sa.Column("display_location_identifier", sa.String(), nullable=False),
        sa.Column("result_index", sa.Integer(), nullable=False),
        sa.Column("max_pages", sa.Integer(), nullable=False, default=1),
        sa.Column("mortgage_rate", sa.Float(), nullable=False, default=0.0515),
        sa.Column("ltv", sa.Float(), nullable=False, default=0.75),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("error_message", sa.String()),
    )
    search_runs.create(bind, checkfirst=True)


def downgrade():
    op.drop_table("search_runs", if_exists=True)
    op.drop_table("users", if_exists=True)
