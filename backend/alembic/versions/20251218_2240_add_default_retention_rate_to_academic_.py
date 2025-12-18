"""add default_retention_rate to academic_level

Revision ID: 0e5370dee317
Revises: 032_rename_budget_terminology
Create Date: 2025-12-18 22:40:20.087782

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0e5370dee317'
down_revision: str | None = '032_rename_budget_terminology'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('ref_academic_levels', sa.Column('default_retention_rate', sa.Numeric(5, 4), nullable=False, server_default='0.96'))


def downgrade() -> None:
    op.drop_column('ref_academic_levels', 'default_retention_rate')
