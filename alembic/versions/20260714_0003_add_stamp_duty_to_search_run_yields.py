"""add stamp duty to search run yields

Revision ID: 20260714_0003
Revises: 20260712_0002
Create Date: 2026-07-14
"""

from alembic import op

revision = "20260714_0003"
down_revision = "20260712_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'ALTER TABLE IF EXISTS search_run_yields ADD COLUMN IF NOT EXISTS "Stamp_Duty" FLOAT'
    )


def downgrade():
    op.execute('ALTER TABLE IF EXISTS search_run_yields DROP COLUMN IF EXISTS "Stamp_Duty"')
